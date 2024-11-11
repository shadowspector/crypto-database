import unittest
from datetime import datetime
from services.chain_service import ChainService, ChainStatus, Chain
from services.database import DatabaseService
from utils.test_helpers import setup_test_db, cleanup_test_db

class TestChainCreation(unittest.TestCase):
    """Test cases for Chain creation functionality"""

    def setUp(self):
        """Set up test database"""
        self.test_db = setup_test_db()
        DatabaseService.execute_query('''
            CREATE TABLE IF NOT EXISTS Chain (
                name TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                status TEXT CHECK(status IN ("active", "inactive", "deprecated", "maintenance")),
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

    def tearDown(self) -> None:
        """Clean up test database"""
        cleanup_test_db()
    
    def test_create_chain(self):
        """Test creating a new chain"""
        result = ChainService.create_chain(
            name='ethereum',
            display_name='Ethereum',
            is_active=True,
            status=ChainStatus.ACTIVE
        )

        self.assertTrue(result['success'])
        self.assertIn('chain', result['data'])

        chain = result['data']['chain']
        self.assertEqual(chain.name, 'ethereum')
        self.assertEqual(chain.display_name, 'Ethereum')
        self.assertTrue(chain.is_active)
        self.assertEqual(chain.status, ChainStatus.ACTIVE)
    
    def test_duplicate_chain(self):
        """Test creating a duplicate chain"""
        ChainService.create_chain('ethereum', 'Ethereum')
        result = ChainService.create_chain('ethereum', 'Ethereum')

        self.assertFalse(result['success'])
        self.assertIn('already exists', result['error'])

class TestChainRerieval(unittest.TestCase):
    """Test cases for chain retrieval functionality"""

    def setUp(self):
        self.test_db = setup_test_db()
        DatabaseService.execute_query('''
        CREATE TABLE IF NOT EXISTS Chain (
            name TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            status TEXT CHACK(status IN ('active', 'inactive', 'deprecated', 'maintenance')),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
            )                              
        ''')

        # Create test chains
        ChainService.create_chain('ethereum', 'Ethereum', True, ChainStatus.ACTIVE)
        ChainService.create_chain('bitcoin', 'Bitcoin', False, ChainStatus.INACTIVE)
        ChainService.create_chain('optimism', 'Optimism', True, ChainStatus.MAINTENANCE)

    def tearDown(self) -> None:
        cleanup_test_db()

    def test_get_chain(self):
        """Test retrieving a chain"""
        result = ChainService.get_chain('ethereum')
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['chain'].name, 'ethereum')

    

    def test_get_active_chains(self):
        """Test retrieving active chains"""
        result = ChainService.get_active_chains()
        self.assertTrue(result['success'])
        chains = result['data']['chains']
        self.assertEqual(len(chains), 2)
        chain_names = {chain.name for chain in chains}
        self.assertEqual(chain_names, {'ethereum', 'optimism'})

    def test_get_chains_by_status(self):
        """Test retrieving chains by status"""
        result = ChainService.get_chains_by_status(ChainStatus.MAINTENANCE)
        self.assertTrue(result['success'])
        chains = result['data']['chains']
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0].name, 'optimism')

class TestChainUpdates(unittest.TestCase):
    """Test cases for chain update functionality"""

    def setUp(self) -> None:
        self.test_db = setup_test_db()
        DatabaseService.execute_query('''
            CREATE TABLE IF NOT EXISTS Chain (
                name TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                status TEXT CHECK(status IN ('active', 'inactive', 'deprecated', 'maintenance')),
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )                         
        ''')
        ChainService.create_chain('ethereum', 'Ethereum')
    
    def tearDown(self) -> None:
        cleanup_test_db()

    def test_update_chain_status(self):
        """Test updating chain status"""
        result = ChainService.update_chain_status(
            name='ethereum',
            is_active=False,
            status=ChainStatus.MAINTENANCE
        )

        self.assertTrue(result['success'])

        chain_result = ChainService.get_chain('ethereum')
        chain = chain_result['data']['chain']
        self.assertFalse(chain.is_active)
        self.assertEqual(chain.status, ChainStatus.MAINTENANCE)


if __name__ == '__main__':
    unittest.main()

    
