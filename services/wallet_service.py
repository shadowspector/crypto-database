from services.database import DatabaseService
from services.moralis_service import MoralisService
from utils.response import ResponseHandler
from utils.logging_config import setup_logger, log_function_call
from models.wallet import WalletItem
from config import Config
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict

logger = setup_logger(__name__)

@dataclass
class TokenError:
    chain: str
    name: str
    error_type: str
    details: str

@dataclass
class TokenDiscovery:
    chain: str
    name: str
    symbol: str
    price: float


class WalletService:

    
    @staticmethod
    @log_function_call(logger)
    def update_wallet_and_prices():
        wallet_address = Config.WALLET_ADDRESS
        aggregated_data = defaultdict(lambda: {'balance': 0, 'price': 0,
                                                'symbol': '', 'alternate_names': set(),
                                                'api_id': ''})
        
        # Track failures and discoveries
        failed_tokens: Dict[str, List[TokenError]] = defaultdict(list)
        new_tokens: List[TokenDiscovery] = []
        zero_price_tokens: List[TokenError] = []

        for chain in Config.CHAINS_TO_QUERY:
            logger.info(f'Fetching wallet data for chain: {chain}')
            response = MoralisService.get_wallet_balances_and_prices(wallet_address, chain)

            if not response['success']:
                logger.error(f'Failed to fetch data for chain: {chain}')
                continue

            data = response['data']
            if not('result' in data and data['result']):
                logger.warning(f'No result data for chain: {chain}')
                continue
            logger.info(f'Processing {len(data["result"])} tokens for chain {chain}')
            for token in data['result']:
                moralis_name = token.get('name', '')

                # Skip deposit tokens
                if moralis_name in Config.DEPOSIT_TOKENS:
                    logger.debug(f'Skipping deposit token: {moralis_name}')
                    continue

                # Skip deposit tokens
                if moralis_name in Config.SPAM_TOKENS:
                    logger.debug(f'Skipping spam token: {moralis_name}')
                    continue

                # Track balance/price parsing errors
                try:
                    balance = float(token.get('balance_formatted',0))
                    price = float(token.get('usd_price', 0))
                except (ValueError, TypeError) as e:
                    failed_tokens['parse_error'].append(
                        TokenError(chain=chain,
                                   name=moralis_name,
                                   error_type='parse_error',
                                   details=f'Failed to parse balance or price: {str(e)}')
                    )
                    continue
                
                if price == 0:
                    zero_price_tokens.append(
                        TokenError(chain=chain,
                                   name=moralis_name,
                                   error_type='no price',
                                   details=f'Token price is 0 (symbol: {token.get("symbol", "N/A")})')
                    )
                    # Continue processing as we still want to track the token

                db_result = WalletService.find_coin_by_name(moralis_name)
                
                if not db_result['success']:
                    # This is a new token discovery, not an error
                    new_tokens.append(
                        TokenDiscovery(
                            chain=chain,
                            name=moralis_name,
                            symbol=token.get('symbol', ''),
                            price=price
                        )
                    )
                    name = moralis_name
                    alt_names_set = {moralis_name}
                    display_name = moralis_name
                    api_id = token.get('token_address', '')
                else:
                    name, display_name, alt_names, api_id = db_result['data'][0]
                    alt_names_set = set(json.loads(alt_names)) if alt_names else set()
                    alt_names_set.add(moralis_name)
                
                # Update aggregated data 
                aggregated_data[name]['balance'] += balance
                aggregated_data[name]['price'] = max(aggregated_data[name]['price'],price)
                aggregated_data[name]['symbol'] = token.get('symbol', '')
                aggregated_data[name]['alternate_names'].update(alt_names_set)
                aggregated_data[name]['api_id'] = api_id or aggregated_data[name]['api_id']
                aggregated_data[name]['display_name'] = display_name
            
        # Update database with aggregated data                
        logger.info(f'Updating databse with aggregated data for {len(aggregated_data)} tokens')
        for name, data in aggregated_data.items():
            try:
                WalletService.update_token(data['display_name'], data['balance'], data['price'])
            except Exception as e:
                failed_tokens['update_error'].append(
                    TokenError(chain='N/A',
                               name=name,
                               error_type='update_error',
                               details=f'Failed to update token: {str(e)}')
                )
        
        # Log summary of token processing
        logger.info('\n=== Token Processing Summary ===')

        # Log new token discoveries
        if new_tokens:
            logger.info('\nNEW TOKENS DISCOVERED:')
            for token in new_tokens:
                if token.price > 0: # Only log tokens with prices as successful discoveries
                        message = f'''
                            Chain: {token.chain}
                            Token: {token.name} ({token.symbol})
                            Price: ${token.price} 
                        '''
                        logger.info(message)

        # Log zero price tokens
        if zero_price_tokens:
            logger.info('\nTOKENS WITH NO PRICE:')
            for token in zero_price_tokens:
                message= f'''
                    Chain: {token.chain}
                    Token: {token.name}
                    {token.details}
                '''
                logger.warning(message)
        # Log actual errors
        if failed_tokens:
            logger.error('\nFAILED TOKENS:')
            for error_type, tokens in failed_tokens.items():
                error_message = f'\n {error_type.upper()} ({len(tokens)} tokens):'
                for token in tokens:
                    error_message += f'''
                        Chain: {token.chain}
                        Token: {token.name}
                        Details: {token.details}
                    '''
                logger.error(error_message)
        logger.info('\n=== End Token Processing Summary ===')

        logger.info('Updated wallet holdings and prices across all chains')
        return ResponseHandler.success('wallet and prices updated successfully')
    
    @staticmethod
    @log_function_call(logger)
    def find_coin_by_name(name):
        logger.debug(f'Searching for coin: {name}')
        query = '''
            SELECT Name, DisplayName, AlternateNames, ApiId
            FROM CoinPrices
            WHERE LOWER(Name) = LOWER(?) OR LOWER(DisplayName) = LOWER(?) OR LOWER(AlternateNames) LIKE LOWER(?)
        '''
        result = DatabaseService.execute_query(query, (name.lower(), name.lower(), f'%{name.lower()}%'))
        if len(result) == 0:
            return ResponseHandler.error('Coin not found')
        return ResponseHandler.success('Coin found', data=result)
    @staticmethod
    @log_function_call(logger)
    def update_token(token_name, holdings, price=None):
        logger.info(f'Updating token: {token_name}')
        try:
            # Check if the token exists in CoinPrices
            display_name = token_name
            coin_result = WalletService.find_coin_by_name(token_name)
            logger.debug(f'DB Result: {coin_result}')
            if coin_result['success']:
                name, display_name, alt_names, api_id = coin_result['data'][0]
                if price is None:
                    price_result = DatabaseService.execute_query('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (name,))
                    if price_result:
                        price = price_result[0][0]
                    else:
                        price = 0
                        logger.warning(f'Price not found for {name} in CoinPrice. Setting price to 0.')
            else:
                if price is None:
                    price = 0
                    logger.warning(f'Token {token_name} not found in CoinPrices. Setting price to 0.')
            
            # Update or insert the token in the Wallet table
            wallet_query = '''
                INSERT OR REPLACE INTO Wallet (Token, Price, Holdings)
                VALUES (?, ?, ?)
            '''
            DatabaseService.execute_query(wallet_query, (display_name, price, holdings))

            # Update the price in CoinPrices table if the token exisits
            if coin_result['success']:
                coinprices_query = '''
                    UPDATE CoinPrices
                    SET CurrentPrice = ?
                    WHERE Name = ?
                '''
                DatabaseService.execute_query(coinprices_query, (price, name))

            logger.info(f'Token {token_name} updated successfully')
            return ResponseHandler.success(f'Token {display_name} updated successfully.')
        except Exception as e:
            logger.error(f'Error updating token {token_name}: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Failed to update token: {str(e)}')


    @staticmethod
    @log_function_call(logger)
    def _update_coin_prices_entry(name, data, existing=False):
        logger.debug(f'Updating CoinPrices entry for {name}')

        
        query = '''
            INSERT OR REPLACE INTO CoinPrices (Name, CurrentPrice, ApiId, DisplayName, AlternateNames)
            VALUES (?, ?, ?, ?, ?)
        '''
        DatabaseService.execute_query(query, (name, data['price'], data['api_id'], data['display_name'], json.dumps(list(data['alternate_names']))))

    @staticmethod
    @log_function_call(logger)
    def get_wallet_items(sort_by='Value', order='desc'):
        logger.info(f'Retrieving wallet items. Sort by: {sort_by}, Order: {order}')
        query = f'''
            SELECT w.Token, w.Price, w.Holdings, w.Value, c.DisplayName, c.Name
            FROM Wallet w
            LEFT JOIN CoinPrices c ON w.Token = c.Name
            ORDER BY {sort_by} {"DESC" if order == "desc" else "ASC"}
        '''
        result = DatabaseService.execute_query(query)
        wallet_items = []
        for row in result:
            wallet_item = WalletItem(
                token=row[4] or row[0], # Use DisplayName if available, otherwise use Name
                price=row[1],
                holdings=row[2],
                value=row[3],
                original_name=row[5] or row[0] # Store the original name for reference
            )
            wallet_items.append(wallet_item)
        logger.debug(f'Retrieved {len(wallet_items)} wallet items')
        return ResponseHandler.success('Wallet items retrieved successfully', data=wallet_items)
    
    
    
    @staticmethod
    def calculate_total_value():
        query = 'SELECT COALESCE(SUM(VALUE), 0) FROM Wallet'
        result = DatabaseService.execute_query(query)
        return result[0][0] if result else 0
    
    @staticmethod
    def calculate_total_portfolio_value():
        # will calc total portfolio value
        # return wallet for now
        return WalletService.calculate_total_value()