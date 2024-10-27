import unittest
from services.coin_price_service import CoinPriceService
from services.database import DatabaseService
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestAlternateNamesCleaning(unittest.TestCase):
    def setUp(self):
        # Create a test database connection if needed
        self.service = CoinPriceService()
        
    def test_individual_name_cleaning(self):
        """Test cleaning of individual name strings"""
        
                
    def test_list_normalization(self):
        """Test normalization of various list formats"""
        test_cases = [
            # Input, Expected Output
            (
                ["['Curve DAO Token']"],
                ["Curve DAO Token"]
            ),
            (
                ["WETH']", "['Ether"],
                ["WETH", "Ether"]
            ),
            (
                ["Odin", "Dejitaru Odin"],
                ["Odin", "Dejitaru Odin"]
            ),
            (
                '["USD Coin"]',
                ["USD Coin"]
            ),
            (
                ["Multiple", "Tokens"],
                ["Multiple", "Tokens"]
            ),
            (
                [],
                []
            ),
            (
                None,
                []
            )
        ]
        
        for input_names, expected in test_cases:
            with self.subTest(input_names=input_names):
                result = self.service._normalize_alternate_names(input_names)
                self.assertEqual(result, expected)

    def test_database_update(self):
        """Test database update with sample data"""
        

def run_tests():
    """Run the test suite with detailed output"""
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAlternateNamesCleaning)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == '__main__':
    run_tests()