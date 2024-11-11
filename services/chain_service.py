from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import List, Dict,Optional, Any
from enum import Enum

from services.database import DatabaseService
from utils.logging_config import setup_logger, log_function_call
from utils.response import ResponseHandler

logger = setup_logger(__name__)

class ChainStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DEPRECATED = 'deprecated'
    MAINTENANCE = 'maintenance'

@dataclass
class Chain:
    """Represents a blaockchain network"""
    name: str
    display_name: str
    is_active: bool
    status: ChainStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert chian to dictionary representation"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'status': self.status.value,
            'create_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ChainService:
    """Service for managing blockchain networks"""

    @staticmethod
    @log_function_call(logger)
    def create_chain(
        name: str,
        display_name: str,
        is_active: bool = True,
        status: ChainStatus = ChainStatus.ACTIVE
    ) -> Dict[str, Any]:
        """
        Create a new chain entry.

        Args:
            name: Unique identifier for the chain
            display_name: Human-readable name
            is_active: Whether the chain is currently active
            status: Current chain status

        Returns:
            Response containing success status and chain data
        """
        try:
            # Validate chain doesn't already exist
            existing = DatabaseService.execute_query(
                'SELECT 1 FROM Chain WHERE name = ?',
                (name,)
            )
            if existing:
                return ResponseHandler.error(f'Chain {name} already exists')
            
            current_time = datetime.utcnow()

            query = '''
                INSERT INTO Chain (
                    name, display_name, is_active, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            '''

            params = (
                name,
                display_name,
                is_active,
                status.value,
                current_time,
                current_time
            )

            DatabaseService.execute_query(query, params)

            logger.info(f'Created new chain: {name}')
            return ResponseHandler.success(
                'Chain created successfully',
                {'chain': Chain(
                    name=name,
                    display_name=display_name,
                    is_active=is_active,
                    status=status,
                    created_at=current_time,
                    updated_at=current_time
                )}
            )
        except Exception as e:
            logger.error(f'Error creating chain: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Failed to create chain: {str(e)}')
         
    @staticmethod
    @log_function_call(logger)
    def get_chain(name: str) -> Dict[str, Any]:
        """
        Retrieve a chain by name.

        Args:
            name: Chain identifier
        
        Returns:
            Response containing chain data
        """
        try:
            query = '''
                SELECT name, display_name, is_active, status,
                created_at, updated_at
                FROM Chain
                WHERE name = ?
            '''
            result = DatabaseService.execute_query(query, (name,))

            if not result:
                return ResponseHandler.error(f'Chain {name} not found')
            
            chain = ChainService._row_to_chain(result[0])
            return ResponseHandler.success('Chain retrieved', {"chain": chain})
        
        except Exception as e:
            logger.error(f'Error retrieving chain {name}: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Failed to retrieve chain: {str(e)}')
        
    @staticmethod
    @log_function_call(logger)
    def update_chain_status(
        name: str,
        is_active: Optional[bool] = None,
        status: Optional[ChainStatus] = None
    ) -> Dict[str, Any]:
        """
        Update chain status.

        Args:
            name: Chain identifier
            is_active: New active status
            status: New chain status

        Returns:
            ResponseHandler

        """
        try:
            if is_active is None and status is None:
                return ResponseHandler.error('No updates provided')
            
            # Verify chain exists
            chain_result = ChainService.get_chain(name)
            if not chain_result['success']:
                return chain_result
            
            updates = []
            params = []
            if is_active is not None:
                updates.append('is_active = ?')
                params.append(is_active)
            if status is not None:
                updates.append('status = ?')
                params.append(status.value)
            
            updates.append('updated_at = ?')
            params.extend([datetime.utcnow(), name])

            query = '''
                UPDATE Chain
                SET {', '.join(updates)}
                WHERE name = ?
            '''

            DatabaseService.execute_query(query, (tuple(params)))

            logger.info(f'Updated status for chain {name}')
            return ResponseHandler.success('Chain status updated successfully')
        
        except Exception as e:
            logger.error(f'Error updating chain {name}: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Failed to update chain: {str(e)}')
        
    
    @staticmethod
    @log_function_call(logger)
    def get_active_chains() -> Dict[str, Any]:
        """
        Get all active chains.

        Returns:
            Response containing list of active chains.
        """
        try:
            query = '''
                SELECT name, display_name, is_active, status,
                created_at, updated_at
                FROM Chain
                WHERE is_active = 1
                ORDER BY name
            '''
            results = DatabaseService.execute_query(query)

            chains = [ChainService._row_to_chain(row) for row in results]
            return ResponseHandler.success(
                f'Retrieved {len(chains)} active chains',
                {'chains': chains}
            )
        except Exception as e:
            logger.error(f'Error retrieving active chains: {str(e)}', exc_info=True)
            return ResponseHandler.error('Failed to retrieve active chains')
    
    @staticmethod
    @log_function_call(logger)
    def get_chains_by_status(status: ChainStatus) -> Dict[str, Any]:
        """
        Get chains by status.

        Args:
            status: Status to filter by

        Returns:
            Response containing filtered chains
        """
        try:
            query = '''
                SELECT name, display_name, is_active, status,
                created_at, updated_at
                FROM Chain
                WHERE status = ?
                ORDER BY name
            '''
            results = DatabaseService.execute_query(query, (status.value,))

            chains = [ChainService._row_to_chain(row) for row in results]
            return ResponseHandler.success(
                f'Retrieved {len(chains)} chains with status {status.value}',
                {'chains': chains}
            )
        except Exception as e:
            logger.error(f'Error retrieving chains by status: {str(e)}', exc_info=True)
            return ResponseHandler.error('Failed to retrieve chains by status')
        
    @staticmethod
    def _row_to_chain(row: sqlite3.Row) -> Chain:
        """Convert a database row to a Chain object"""
        return Chain(
            name=row['name'],
            display_name=row['display_name'],
            is_active=bool(row['is_active']),
            status=ChainStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )



