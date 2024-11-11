import sqlite3, threading
from sqlite3 import Connection
from typing import Any, List, Optional, Dict, Union
from contextlib import contextmanager
from threading import Lock, local
import queue
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from config import Config
from utils.logging_config import setup_logger

logger = setup_logger(__name__)

@dataclass
class QueryMetrics:
    """Tracks query performance metrics"""
    query: str
    params: tuple
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def duration_ms(self) -> float:
        """Calculate query duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0

class DatabaseConnection:
    """Manages a single database connection with transaction support"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[Connection] = None
        self.transaction_level = 0
        self._lock = threading.Lock()

    def __enter__(self) -> Connection:
        self.connect()
        return self.conn
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
    
    def connect(self) -> None:
        """Create a new database connection"""
        if not self.conn:
            self.conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.conn.row_factory = sqlite3.Row
    
    def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            if self.transaction_level > 0:
                self.conn.rollback()
            self.conn.close()
            self.conn = None
            self.transaction_level = 0
        
    @contextmanager
    def transaction(self):
        """
        Transaction context manager supporting nested transactions.
        Only commit when the outermost transaction exits successfully.
        """
        if not self.conn:
            self.connect()
            
        with self._lock:
            self.transaction_level += 1
        
        try:
            yield self.conn

            with self._lock:
                self.transaction_level -= 1
                if self.transaction_level == 0:
                    self.conn.commit()

        except Exception:
            with self._lock:
                if self.transaction_level > 0:
                    self.conn.rollback()
                self.transaction_level = 0
            raise


class ConnectionPool:
    """Manages a pool of database connections"""

    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._local = threading.local()
        self._lock = threading.Lock()

    def get_connection(self) -> DatabaseConnection: # type: ignore
        """Get a connection from the pool"""
        if not hasattr(self._local, 'connection'):
            with self._lock:
                self._local.connection = DatabaseConnection(self.db_path)
                self._local.connection.connect()
        return self._local.connection
        
    def close_all(self) -> None:
        """Close all connections in the pool"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
            
class DatabaseService:
    """Enhanced database service with connection pooling and transaction management"""

    _pool: Optional[ConnectionPool] = None
    _lock: Lock = threading.Lock()
    _initialized: bool = False

    @classmethod
    def initialize(cls, db_path: str = None, max_connections: int = 5) -> None:
        """Initialize the database service"""
        if not cls._initialized:
            with cls._lock:
                if not cls._initialized:
                    try:

                        db_path = db_path or Config.DATABASE
                        if not db_path:
                            raise ValueError('database path must be specified')

                        # Create database directory if it doesn't exist
                        db_dir = Path(db_path).parent
                        db_dir.mkdir(exist_ok=True)

                        # initialize connection pool
                        cls._pool = ConnectionPool(db_path, max_connections)

                        # Test connection
                        with cls.get_connection() as conn:
                            if not conn:
                                raise RuntimeError('Failed to create database connection')
                            
                        cls._initialized = True
                        logger.info(f'Initialized database connection pool with {max_connections} connections')
                    
                    except Exception as e:
                        cls._pool = None
                        cls._initialized = False
                        logger.error(f'Failed to initialize database: {str(e)}')
                        raise RuntimeError(f'Database initialization failed: {str(e)}') from e
    
    @classmethod
    def get_pool(cls) -> ConnectionPool:
        """Get the connection pool, initializing if necessary"""
        if not cls._initialized:
            cls.initialize()
        if not cls._pool:
            raise RuntimeError('Database pool is not initialized')
        return cls._pool

    @classmethod
    def get_connection(cls) -> DatabaseConnection: # type: ignore
        """Get a database connection, initializing if necessary"""
        if not cls._initialized:
            cls.initialize()
        return cls._pool.get_connection()
        

    @classmethod
    def execute_query(
        cls,
        query: str,
        params: tuple = None,
        fetch: bool = True
    ) -> Union[List[sqlite3.Row], None]:
        """
        Exectue a query and optionally fetch results.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch and return results

        Returns:
            Query results if fetch=True, None otherwise
        """

        metrics = QueryMetrics(
            query=query,
            params=params or tuple(),
            start_time=datetime.utcnow()
        )

        try:
            conn = cls.get_connection()
            with conn:
                cursor = conn.execute(query, params or ())
                if fetch:
                    results = cursor.fetchall()
                    metrics.end_time = datetime.utcnow()
                    cls._log_metrics(metrics)
                    return results

                metrics.end_time = datetime.utcnow()
                cls._log_metrics(metrics)
                return None
            
        except Exception as e:
            metrics.error = str(e)
            metrics.end_time = datetime.utcnow()
            cls._log_metrics(metrics)
            logger.error(f'Database error executing query: {str(e)}', exc_info=True)
            if fetch:
                return []
            return None

    @classmethod
    def execute_transaction(cls, queries: List[Dict[str, Any]]) -> None:
        """
        Execute multiple queries in a single transaction.

        Args:
            queries: List of dicts with 'query' and optional 'params' keys
        """
        try:
            conn = cls.get_connection()
            with conn:
                for query_dict in queries:
                    query = query_dict['query']
                    params = query_dict.get('params', None)
                    conn.execute(query, params or ())
            return True
        except Exception as e:
            logger.error(f'Transaction failed: {str(e)}', exc_info=True)
            return False

    @classmethod
    def _log_metrics(cls, metrics: QueryMetrics) -> None:
        """Log query performance metrics"""
        log_msg = (
            f'Query executed in {metrics.duration_ms:.2f}ms | '
            f'Query: {metrics.query} | '
            f'Params: {metrics.params}'
        )

        if metrics.error:
            logger.error(f'{log_msg} | Error: {metrics.error}')
        elif metrics.duration_ms > 1000: #Log slow queries as warnings
            logger.warning(f'Slow query detected | {log_msg}')
        else:
            logger.debug(log_msg)

    @classmethod
    def cleanup(cls) -> None:
        """Clean up database connections"""
        if cls._pool:
            cls._pool.close_all()
            cls._pool = None
    