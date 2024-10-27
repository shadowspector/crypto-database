from services.coin_price_service import CoinPriceService
from utils.backup_utils import backup_database, restore_database
from services.database import DatabaseService
import json



def run_production_fix():
    ''' Run the alternate names fix on production database '''

    def display_entries(entries, title):
        '''Helper to display entries consistently'''
        print(f'\n=== {title} ===')
        print(f'Found {len(entries)} entries with alternate names:')
        for name, alt_names in entries:
            try:
                if alt_names.startswith('['):
                    try:
                        parsed = json.loads(alt_names)
                        print(f'{name}: {parsed}')
                    except json.JSONDecodeError:
                        print(f'{name}: {alt_names} (malformed JSON)')
                else:
                    print(f'{name}: {alt_names} (raw string)')
            except Exception as e:
                print(f'{name}: {alt_names} (error: {str(e)})')
    
    try:
        # Show current state
        print('\n=== Current State ===')
        query = '''
            SELECT Name, AlternateNames
            FROM CoinPrices
            WHERE AlternateNames != '[]'
            AND length(AlternateNames) > 2
        '''

        current_state = DatabaseService.execute_query(query)
        display_entries(current_state, 'Current State')


        # Confirm proceed
        response = input('\nProceed with fix? (yes/no): ')
        if response.lower() != 'yes':
            print('Operation cancelled')
            return
        
        # Create backup
        print('\n=== Creating Backup ===')
        backup_path = backup_database()
        if not backup_path:
            print('Backup failed. Aborting.')
            return
        print(f'Backup created at: {backup_path}')

        # Run fix
        print('\n=== Running Fix ===')
        CoinPriceService.fix_alternate_names_in_db()

        # Verify results
        print('\n=== Verifying Results ===')
        updated_state = DatabaseService.execute_query(query)
        display_entries(updated_state, 'Updated State')
        
        
        print('\n=== Fix complete ===')
        print(f'Backup Location: {backup_path}')
        print('\nTo restore from backup if needed:')
        print(f'from utils.backup_utils import restore_database')
        print(f'restore_database("{backup_path}")')
    except Exception as e:
        print(f'\n Error during fix: {type(e).__name__}: {str(e)}')
        if 'backup_path' in locals():
            print(f'\nTo restore from backup:')
            print(f'from utils.backup_utils import restore_database')
            print(f'restore_database("{backup_path}")')
        
if __name__ == '__main__':
    run_production_fix()