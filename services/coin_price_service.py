from services.database import DatabaseService
from services.coin_gecko import CoinGeckoService
from services.table_uniformity_manager import TableUniformityManager
from utils.response import ResponseHandler
from utils.logging_config import setup_logger, log_function_call
from models.coin import Coin
from typing import List
import json, re

logger = setup_logger(__name__)

class CoinPriceService:
    @staticmethod
    def _normalize_alternate_names(names) -> List[str]:
        '''
        Normalize alternate names to ensure consistent format.
        Returns a clean list of strings without nested lists or extra quotes.
        '''

        if not names:
            return []
        
        # already a clean list of strings
        if isinstance(names, list) and all(isinstance(x, str) for x in names):
            return [
                CoinPriceService._clean_name(name)
                for name in names
                if name
            ]
        
        # Handle string input
        if isinstance(names, str):
            try:
                # Try parsing as JSON
                parsed = json.loads(names)
                if isinstance(parsed,list):
                    # Clean each name in the parsed list
                    return [
                        CoinPriceService._clean_name(name)
                        for name in parsed
                        if name
                    ]
                # Single value
                return [CoinPriceService._clean_name(str(parsed))]
            except json.JSONDecodeError:
                # If it looks like a list but couldn't be parsed as JSON
                if names.startswith('[') and names.endswith(']'):
                    # Split by comman and clean each part
                    parts = re.split(r',\s*', names[1:-1])
                    return [
                        CoinPriceService._clean_name(part)
                        for part in parts
                        if part.strip()
                    ]
                # Single Value
                return [CoinPriceService._clean_name(names)]
                
        return []


    @staticmethod
    def get_all_coins(sort_by='MarketCap', order='desc'):
        query = f'SELECT * FROM CoinPrices ORDER BY {sort_by} {"DESC" if order == "desc" else "ASC"}'
        result = DatabaseService.execute_query(query)
        coins = []
        for row in result:
            coin_dict = dict(zip(['Name', 'CurrentPrice', 'MarketCap', 'MarketCapRank', 'TotalVolume', 'High24h', 'Low24h',
                                  'PriceChange24h', 'PriceChangePercentage24h', 'MarketCapChange24h', 'MarketCapChangePercentage24h',
                                  'PriceChangePercentage1h', 'DisplayName', 'ApiId', 'AlternateNames'], row))
            
            # Clean up alternate names
            coin_dict['AlternateNames'] = CoinPriceService._normalize_alternate_names(
                coin_dict['AlternateNames']
            )

            coins.append(Coin.from_dict(coin_dict))
            
            
            
        return ResponseHandler.success('Coins retrieved successfully', data=coins)
    
    @staticmethod
    def update_coin_prices():
        logger.info('Starting coin price update')
        response = CoinGeckoService.fetch_coin_prices()
        if not response['success']:
            logger.error('Failed to fetch coin prices from CoinGecko')
            return ResponseHandler.error('Failed to fetch coin prices')
        
        coins = response['data']
        logger.info(f'Fetched {len(coins)} coins from CoinGecko')

        top_500_coins = set()
        updated_count = 0
        for coin_data in coins:
            try:
                coin = Coin(
                    Name=coin_data['name'],
                    CurrentPrice=coin_data['current_price'],
                    MarketCap=coin_data['market_cap'],
                    MarketCapRank=coin_data['market_cap_rank'],
                    TotalVolume=coin_data['total_volume'],
                    High24h=coin_data['high_24h'],
                    Low24h=coin_data['low_24h'],
                    PriceChange24h=coin_data['price_change_24h'],
                    PriceChangePercentage24h=coin_data['price_change_percentage_24h'],
                    MarketCapChange24h=coin_data['market_cap_change_24h'],
                    MarketCapChangePercentage24h=coin_data['market_cap_change_percentage_24h'],
                    PriceChangePercentage1h=coin_data['price_change_percentage_1h_in_currency'],
                    ApiId=coin_data['id'],
                    DisplayName=coin_data['name'],
                    AlternateNames=[] # init - changed later
                )
                top_500_coins.add(coin.Name)
                CoinPriceService._update_coin_in_db(coin)
                updated_count += 1
            except KeyError as e:
                logger.error(f'Failed to process coin data for {coin_data.get("name", "Unknown")}: Missing key {str(e)}')
            except Exception as e:
                logger.error(f'Failed to update price for {coin_data.get("name", "Unknown")}: {str(e)}')
            
        logger.info(f'Updated {updated_count} coins from top 500 list')
        # Fetch all coins
        all_db_coins = DatabaseService.execute_query('SELECT Name, ApiId FROM CoinPrices')
        logger.info(f'Fetch {len(all_db_coins)} coins from database for additional updates')

        additional_updates = 0
        for name, api_id in all_db_coins:
            if (name not in top_500_coins) and api_id:
                logger.info(f'Fetching data for {name} (API ID: {api_id})')
                response = CoinGeckoService.fetch_single_coin_price(api_id)
                if response['success']:
                    coin_data = response['data']
                    coin = Coin(
                        Name=coin_data['name'],
                        CurrentPrice=coin_data['market_data']['current_price']['usd'],
                        MarketCap=coin_data['market_data']['market_cap']['usd'],
                        MarketCapRank=coin_data['market_data'].get('market_cap_rank', 0),
                        TotalVolume=coin_data['market_data']['total_volume'].get('usd',0),
                        High24h=coin_data['market_data']['high_24h'].get('usd', 0),
                        Low24h=coin_data['market_data']['low_24h'].get('usd', 0),
                        PriceChange24h=coin_data['market_data'].get('price_change_24h',0),
                        PriceChangePercentage24h=coin_data['market_data'].get('price_change_percentage_24h',0),
                        MarketCapChange24h=coin_data['market_data'].get('market_cap_change_24h',0),
                        MarketCapChangePercentage24h=coin_data['market_data'].get('market_cap_change_percentage_24h',0),
                        PriceChangePercentage1h=coin_data['market_data'].get('price_change_percentage_1h_in_currency', []).get('usd',0),
                        ApiId=api_id,
                        DisplayName=coin_data['name'],
                        AlternateNames=[]
                    )
                    CoinPriceService._update_coin_in_db(coin)
                    additional_updates += 1
                else:
                    logger.warning(f'Failed to update data for {name} (API ID: {api_id})')
        logger.info(f'Updated and additional {additional_updates} coins not in top 500')
        logger.info(f'Finished updating coin prices. Total updates: {updated_count + additional_updates}')
        return ResponseHandler.success('Coin prices updated successfully')
        
    
        
    @staticmethod
    def update_coin_names(coin_name, new_alternate_names, new_display_name, api_id):
        try:
            # Get current display name
            query = 'SELECT DisplayName FROM CoinPrices WHERE Name = ?'
            result = DatabaseService.execute_query(query, (coin_name, ))
            if not result:
                return ResponseHandler.error('Coin not found')
            
            current_display_name = result[0][0]

            # Update CoinPrices table
            update_query = '''UPDATE CoinPrices
                            SET AlternateNames = ?,
                                DisplayName = ?,
                                ApiId = ?
                            WHERE Name = ?'''
            params = (json.dumps(new_alternate_names), new_display_name, api_id, coin_name)
            DatabaseService.execute_query(update_query, params)

            # Update the name in all other tables only if the display name has changed
            if current_display_name != new_display_name:
                TableUniformityManager.update_coin_display_name(current_display_name, new_display_name)
                return ResponseHandler.success('Display name updated successfully across all tables')
            else:
                return ResponseHandler.success("Coin information updated successfully")
        except Exception as e:
            return ResponseHandler.error(str(e))
        
    @staticmethod
    def find_token(token):
        query = '''
            SELECT ApiId, DisplayName, CurrentPrice
            FROM CoinPrices
            WHERE LOWER(ApiId) = LOWER(?) OR LOWER(Name) = LOWER(?) OR LOWER(?) OR LOWER(DisplayName) = LOWER(?)
        '''
        result = DatabaseService.execute_query(query, (token.lower(), token.lower(), token.lower()))
        if result:
            return ResponseHandler.success('Token found', data=result[0])
        return ResponseHandler.error('Token not found')
    
    @staticmethod
    def find_coin_by_name(name):
        query = '''
            SELECT Name, DisplayName, AlternameNames, ApiId
            FROM CoinPrices
            WHERE LOWER(Name) = LOWER(?) OR LOWER(DisplayName) = LOWER(?) OR LOWER(AlternateNames) LIKE LOWER(?)
        '''
        result = DatabaseService.execute_query(query, (name.lower(), name.lower(), f'%{name.lower()}%'))
        if result:
            return ResponseHandler.success('Coin found', data=result[0])
        return ResponseHandler.error('Coin not found')
    
    @staticmethod
    @log_function_call(logger)
    def insert_or_update_coin(api_id):
        response = CoinGeckoService.fetch_single_coin_price(api_id)
        if not response['success']:
            logger.error(f'Failed to fetch coin data for {api_id}')
            return ResponseHandler.error('Failed to fetch coin data')
        
        coin_data = response['data']
        logger.info('Succefully located coin')
        coin = Coin(
            Name=coin_data['name'],
            CurrentPrice=coin_data['market_data']['current_price']['usd'],
            MarketCap=coin_data['market_data']['market_cap']['usd'],
            MarketCapRank=coin_data['market_cap_rank'],
            TotalVolume=coin_data['market_data']['total_volume']['usd'],
            High24h=coin_data['market_data']['high_24h']['usd'],
            Low24h=coin_data['market_data']['low_24h']['usd'],
            PriceChange24h=coin_data['market_data']['price_change_24h'],
            PriceChangePercentage24h=coin_data['market_data']['price_change_percentage_24h'],
            MarketCapChange24h=coin_data['market_data']['market_cap_change_24h'],
            MarketCapChangePercentage24h=coin_data['market_data']['market_cap_change_percentage_24h'],
            PriceChangePercentage1h=coin_data['market_data']['price_change_percentage_1h_in_currency']['usd'],
            DisplayName=coin_data['name'],
            ApiId=api_id,
            AlternateNames=[]
        )

        CoinPriceService._update_coin_in_db(coin)
        logger.info(f'Token {coin.DisplayName} updated successfully')
        return ResponseHandler.success('Coin updated successfully')
    
    @staticmethod
    def update_manual_token(token_name, token_price):
        try:
            query = '''
                INSERT OR REPLACE INTO CoinPrices (Name, CurrentPrices, MarketCap, MarketCapRank, TotalVolume,
                                                    High24h, Low24h, PriceChange24h, PriceChangePercentage24h,
                                                    MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
                                                    DisplayName, ApiId)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (token_name, token_price, 0, 0, 0, token_price, token_price, 0, 0, 0, 0, 0, token_name, '')
            DatabaseService.execute_query(query, params)
            return ResponseHandler.success('Manual token updated successfully')
        except Exception as e:
            return ResponseHandler.error(str(e))
        
    @staticmethod
    @log_function_call(logger)
    def _update_coin_in_db(coin):    
        existing_data = DatabaseService.execute_query('SELECT ApiId, DisplayName, AlternateNames FROM CoinPrices WHERE Name = ?', (coin.Name,))
        if existing_data:
            coin.ApiId = existing_data[0][0] or coin.ApiId
            coin.DisplayName = existing_data[0][1] or coin.DisplayName

            # Merge and normalize alternate names
            existing_names = CoinPriceService._normalize_alternate_names(existing_data[0][2])
            coin.AlternateNames = list(set(existing_names + coin.AlternateNames))

        # Prepare clean alternate names for storage
        alternate_names_json = json.dumps([
            name.strip("'\"") for name in coin.AlternateNames if name
        ])

        query = '''
        INSERT OR REPLACE INTO CoinPrices (
            Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
            PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h,
            PriceChangePercentage1h, DisplayName, ApiId, AlternateNames
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        

        params = (
            coin.Name, coin.CurrentPrice, coin.MarketCap, coin.MarketCapRank, coin.TotalVolume, coin.High24h, coin.Low24h,
            coin.PriceChange24h, coin.PriceChangePercentage24h, coin.MarketCapChange24h,
            coin.MarketCapChangePercentage24h, coin.PriceChangePercentage1h,
            coin.DisplayName, coin.ApiId, alternate_names_json
        )

        DatabaseService.execute_query(query, params)
        logger.info(f'Updated/Inserted coin: {coin.Name} with alternate Names: {alternate_names_json}')
        #logging.debug(f'Inserted data: {json.dumps(dict(zip(query.split("(")[1].split(")")[0].split(", "), params)), indent=2)}')

                
    @staticmethod
    def _clean_name(name: str) -> str:
        '''
        Clean a single name string by removing extra quotes, brackets, and whitespace

        Args:
            name: The name string to clean
        
        Returns:
            A cleaned string with no extra quotes, brackets, or whitespace
        '''
        if not name:
            return ''
        
        # Handle nested structure case
        if '][' in name:
            parts = [part.strip("[]'\"") for part in name.split('][')]
            return ' '.join(filter(None, map(str.strip, parts)))
        
        # Normal Case
        cleaned = name.strip("[]'\"")
        cleaned = cleaned.strip()

        return cleaned
        
    
    @staticmethod
    def fix_alternate_names_in_db(table_name='CoinPrices'):
        '''
        Fix alternate names in the specified table.

        Args:
            table_name (str): Name of the table to fix (default: "CoinPrices")
        '''

        
        query = f'''
        SELECT Name, AlternateNames
        FROM {table_name}
        WHERE AlternateNames IS NOT NULL
        AND AlternateNames != "[]"
        AND length(AlternateNames) > 2
        '''
        rows = DatabaseService.execute_query(query)

        
        logger.info(f'Found {len(rows)} rows with non-empty alternate names')

        for name, alternate_names in rows:

            logger.info(f'Processing {name}: {alternate_names!r}')
            cleaned_names = []
            try:
                if not alternate_names.startswith('['):
                    cleaned = CoinPriceService._clean_name(alternate_names)
                    if cleaned:
                        cleaned_names = [cleaned]
                else:
                    # Try to parse as JSON

                    
                    try:
                        parsed_names = json.loads(alternate_names)
                        if isinstance(parsed_names, list):
                            for item in parsed_names:
                                cleaned = CoinPriceService._clean_name(str(item))
                                if cleaned:
                                    cleaned_names.append(cleaned)
                        else:
                            cleaned = CoinPriceService._clean_name(str(parsed_names))
                            if cleaned:
                                cleaned_names = [cleaned]
                            
                    except json.JSONDecodeError:
                        # If not valid JSON, treat as a raw string
                        logger.warning(f'Non-JSON data found for {name}, treating as raw string')
                        cleaned = CoinPriceService._clean_name(alternate_names)
                        if cleaned:
                            cleaned_names = [cleaned]
                    
                    # Remove duplicates while preserving order
                    cleaned_names = list(dict.fromkeys(cleaned_names))

                    # Convert to JSON string
                    cleaned_json = json.dumps(cleaned_names)

                    
                    # Update if changed
                    if cleaned_names != alternate_names:
                        update_query = f'UPDATE {table_name} SET AlternateNames = ? WHERE Name = ?'
                        DatabaseService.execute_query(update_query, (cleaned_json, name))
                        logger.info(f'Updated {name}:')
                        logger.info(f'Original: {alternate_names}')
                        logger.info(f'Cleaned: {cleaned_names}')
                    else:
                        logger.info(f'No changes needed for {name}')
                
            except Exception as e:
                logger.error(f'Error processing {name}: {type(e).__name__}: {str(e)}')
                logger.error(f'Raw Value: {alternate_names!r}')
                continue
                    