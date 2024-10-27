from services.database import DatabaseService

def setup_test_db():
    """Set up test database tables"""
    DatabaseService.execute_query('''
        CREATE TABLE IF NOT EXISTS TestCoinPrices(
            Name TEXT PRIMARY KEY,
            AlternateNames TEXT,
            CurrentPrice REAL
        )              
    ''')
def cleanup_test_db():
    ''' Clean up test database tables '''
    DatabaseService.execute_query('DROP TABLE IF EXISTS TestCoinPrices')
