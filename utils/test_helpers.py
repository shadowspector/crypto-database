from pathlib import Path
import os
from services.database import DatabaseService

def setup_test_db():
    """Set up test database tables"""
    
    # Creat test database path
    test_db = str(Path('test_database.db').absolute())

    # Remove existing test database if exists
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # init db service with test db
    DatabaseService.initialize(test_db)

    # Verify initialization succeeded
    if not DatabaseService._initialized or not DatabaseService._pool:
        raise RuntimeError('Database initizalization failed')
    
    return test_db



def cleanup_test_db():
    ''' Clean up test database tables '''
    DatabaseService.cleanup()
    test_db =str(Path('test_database.db').absolute())
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception as e:
        print(f'Warning: Failed to remove test database: {e}')

    