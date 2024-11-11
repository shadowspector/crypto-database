import unittest
import sqlite3, os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import List

from services.database import DatabaseService
from config import Config

class TestDatabaseService(unittest.TestCase):
    """"test cases for enhanced DatabaseService"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""

        # Create test database path
        cls.test_db = str(Path('test_database.db').absolute())

        # Ensure database directory exists
        db_dir = Path(cls.test_db).parent
        db_dir.mkdir(exist_ok=True)

        # Initialize database service with test database
        DatabaseService.initialize(cls.test_db)

        # Verify initialization succeeded
        if not DatabaseService._initialized or not DatabaseService._pool:
            raise RuntimeError('Database initialization failed')
        
        # Create test table
        with DatabaseService.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )                
            ''')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        DatabaseService.cleanup()
        try:
            if os.path.exists(cls.test_db):
                os.remove(cls.test_db)
        except Exception as e:
            print(f'Warning: Failed to remove test database: {e}')


    def setUp(self):
        """Clear test table before each test"""
        DatabaseService.execute_query('DELETE FROM test_table')

    def test_basic_query_execution(self):
        """Test basic query execution"""
        # Insert test data
        DatabaseService.execute_query(
            'INSERT INTO test_table (name, value) VALUES (?, ?)',
            ('test', 123.45)
        )

        # Query data
        result = DatabaseService.execute_query(
            'SELECT * FROM test_table WHERE name = ?',
            ('test',)
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test')
        self.assertEqual(result[0]['value'], 123.45)

    def test_transaction_management(self):
        """Test transaction management"""
        try:
            DatabaseService.execute_transaction([
                {
                    'query': 'INSERT INTO test_table (name, value) VALUES (?, ?)',
                    'params': ('test1', 100)
                },
                {
                    'query': 'INSERT INTO test_table (name, value) VALUES (?, ?)',
                    'params': ('test2', 200)
                }
            ])
        except Exception:
            self.fail('Transaction failed unexpectedly')
        
        result = DatabaseService.execute_query('SELECET COUNT(*) as count FROM test_table')
        self.assertEqual(result[0]['count'], 2)

    def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        with self.assertRaises(sqlite3.Error):
            DatabaseService.execute_transaction([
                {
                    'query': 'INSERT INTO test_table (name, value) VALUES (?, ?)',
                    'params': ('test1', 100)
                },
                {
                    'query': 'INSERT INTO invalid_tabel (name) VALUES (?)',
                    'params': ('test2',)
                }
            ])

        result = DatabaseService.execute_query('SELECT COUNT(*) as count FROM test_table')
        self.assertEqual(result[0]['count'], 0)

    def test_concurrent_access(self):
        """Test concurrent database access"""
        def insert_record(i: int) -> None:
            DatabaseService.execute_query(
                'INSERT INTO test_table (name, value) VALUES (?, ?)',
                (f'test{i}', i)
            )

        # Create multiple threads to insert records
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(insert_record, range(10))

        result = DatabaseService.execute_query('SELECT COUNT(*) as count FROM test_table')
        self.assertEqual(result[0]['count'], 10)

    def test_connection_reuse(self):
        """Test that connections are being reused"""
        connection_ids = set()

        for _ in range(10):
            with DatabaseService.get_connection() as db:
                connection_ids.add(id(db))

        # Should have fewer unique connections than operations
        self.assertLess(len(connection_ids), 10)

if __name__ == '__main__':
    unittest.main()
    
        