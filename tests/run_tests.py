import unittest
import sys
from pathlib import Path

def run_test_suite():
    '''
    Run the complete test suite with detailed output
    '''

    # Add project root to path to ensure imports work
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))

    # Create test loader
    loader = unittest.TestLoader()

    # Load tests from test directory
    test_dir = Path(__file__).parent
    suite = loader.discover(
        start_dir=str(test_dir),
        pattern='test_*.py'
    )

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return True if all tests passed
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)