# test/test_cooin_price.py
import unittest
from services.coin_price_service import CoinPriceService
from services.database import DatabaseService
import json
import logging
from utils.test_helpers import setup_test_db, cleanup_test_db

class TestCoinPriceService(unittest.TestCase):
    """Tests for CoinPriceService"""

    def setUp(self):
        self.service = CoinPriceService()
        setup_test_db()
    
    def tearDown(self):
        cleanup_test_db()
    
    def test_clean_name(self):
        """Test name cleaning functionality"""
        print('\n=== Testing Individual Name Cleaning ===')
        test_cases = [
            ("['Curve DAO Token']", "Curve DAO Token"),
            ("WETH']", "WETH"),
            ("['Ether", "Ether"),
            ("'USD Coin'", "USD Coin"),
            ("  Spaced Token  ", "Spaced Token"),
            ("['Nested']['Token']", "Nested Token")
        ]
        
        for input_name, expected in test_cases:
            print(f'\nInput: {input_name!r}')
            # Call the method through the instance
            result = CoinPriceService._clean_name(input_name)
            print(f'Result: {result!r}')
            print(f'Expected: {expected!r}')
            self.assertEqual(result, expected)
    
    def test_alternate_names_db(self):
        """Test database operations for alternate names"""
        print('\n=== Testing Database Update ===')
        try:
            # Create test table
            print('\nCreating test table...')
            DatabaseService.execute_query('''
                CREATE TABLE IF NOT EXISTS TestCoinPrices (
                    Name TEXT PRIMARY KEY,
                    AlternateNames TEXT,
                    CurrentPrice REAL
                )
            ''')

            # Clear any existing test data
            DatabaseService.execute_query('DELETE FROM TestCoinPrices')

            # Prepare test data
            test_data = [
                ("Token1", json.dumps(["Curve DAO Token"])),
                ("Token2", json.dumps(["WETH", "Ether"])),
                ("Token3", json.dumps(["Clean", "Names"])),
                ("Token4", json.dumps([])) 
            ]
            
            # Insert test data
            print("\nInserting test data...")
            for name, alt_names in test_data:
                print(f'Inserting: {name} with {alt_names}')
                query = """
                    INSERT INTO TestCoinPrices (Name, AlternateNames, CurrentPrice) 
                    VALUES (?, ?, 1.0)
                """
                DatabaseService.execute_query(query, (name, alt_names))

            # Verify insertion
            print('\nVerifying inserted data...')
            results = DatabaseService.execute_query("SELECT Name, AlternateNames FROM TestCoinPrices")
            for name, alt_names in results:
                print(f'Stored: {name}: {alt_names!r}')

            # Run the fix
            print('\nRunning database fix...')
            self.service.fix_alternate_names_in_db('TestCoinPrices')
            
            # Verify results
            print('\nVerifying results...')
            expected_results = {
                "Token1": ["Curve DAO Token"],
                "Token2": ["WETH", "Ether"],
                "Token3": ["Clean", "Names"],
                "Token4": []
            }
            
            for name, expected in expected_results.items():
                result = DatabaseService.execute_query(
                    "SELECT AlternateNames FROM TestCoinPrices WHERE Name = ?",
                    (name,)
                )
                
                
                stored = result[0][0] if result else None
                print(f'\nChecking {name}:')
                print(f'Stored Value: {stored!r}')
                print(f'Expected: {expected!r}')

                
                try:
                    stored_names = json.loads(stored) if stored else []
                    self.assertEqual(stored_names, expected)
                except json.JSONDecodeError as e:
                    self.fail(f'Failed to parse JSON for {name}: {e}, value: {stored!r}')
                
        except Exception as e:
            print(f'\nTest failed with error: {type(e).__name__}: {str(e)}')
            raise
        finally:
            # Clean up
            print('\nCleaning up test data...')
            DatabaseService.execute_query("DROP TABLE IF EXISTS TestCoinPrices")
        
