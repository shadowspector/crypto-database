import pytest
import sys
from pathlib import Path
import argparse
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests(args):
    '''
    Run the test suite with specified options

    Args:
        args: Parsed command line arguments
    
    Returns:
        bool: True if all tests passed
    '''
    try:
        # Add project root to path to ensure imports work
        project_root = Path(__file__).parent.parent
        sys.path.append(str(project_root))

        # Build pytest arguments
        pytest_args = ['tests/']

        if args.verbose:
            pytest_args.append('-v')
        if args.show_output:
            pytest_args.append('-s')
        if args.coverage:
            pytest_args.extend(['--cov=services', '--cov-report=term-missing'])
        if args.specific_test:
            pytest_args = [args.specific_test]
        
        # Run tests
        logger.info('Starting test run...')
        result = pytest.main(pytest_args)

        success = result == pytest.ExitCode.OK
        if success:
            logger.info('All tests passed successfully!')
        else:
            logger.error('Some tests failed.')
        
        return success
        
    except Exception as e:
        logger.error(f'Error running tests: {str(e)}', exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description='Run the test suite')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-s', '--show-output', action='store_true', help='Show print statements during tests')
    parser.add_argument('-c', '--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('-t', '--specific-test', help='Run a specific test file or class')

    args = parser.parse_args()

    success = run_tests(args)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
    
    
    

    