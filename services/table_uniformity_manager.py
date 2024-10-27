from services.database import DatabaseService

class TableUniformityManager:
    @staticmethod
    def update_coin_display_name(old_display_name, new_display_name):
        tables_to_update = [
            ('Wallet', 'Token'),
            ('Staking', 'Token'),
            ('Farming', 'TokenA'),
            ('Farming', 'TokenB'),
            ('LeveragedFarming', 'TokenA'),
            ('LeveragedFarming', 'TokenB'),
            ('LendingBorrowing', 'Asset')
        ]
    
        for table, column in tables_to_update:
            query = f'''
                UPDATE {table}
                SET {column} = ?
                WHERE {column} = ?
            '''
            DatabaseService.execute_query(query, (new_display_name, old_display_name))
    
    @staticmethod
    def update_coin_names_in_all_tables(updates):
        '''
        Updates coin names across all relevant tables.

        :param updates: A list of tuples, each containing (old_name, new_name)
        '''
        for old_name, new_name in updates:
            TableUniformityManager.update_coin_name(old_name, new_name)

    
