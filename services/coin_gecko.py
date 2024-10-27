import requests, time, json
from config import Config
from utils.response import ResponseHandler
from utils.logging_config import setup_logger, log_function_call

logger = setup_logger(__name__)

class CoinGeckoService:
    BASE_URL = 'https://api.coingecko.com/api/v3'

    @staticmethod
    @log_function_call(logger)
    def fetch_coin_prices():
        url = f'{CoinGeckoService.BASE_URL}/coins/markets'
        all_coins = []
        total_top_coins = 500
        coins_per_page = 100

        for page in range(1, (total_top_coins // coins_per_page) + 1):
            params = {
                'x_cg_demo_api_key': Config.CG_API_KEY,
                'vs_currency': 'usd',
                'order' : 'market_cap_desc',
                'per_page' : coins_per_page,
                'page' : page,
                'sparkline' : 'false',
                'price_change_percentage' : '1h,24h',
            }
            logger.info(f'Fetching coin prices from CoinGecko API - Page {page}')
            response = CoinGeckoService._make_request(url, params=params)

            if response['success']:
                all_coins.extend(response['data'])
                logger.info(f'Successfully fetch {len(response["data"])} coins from page {page}')
            else:
                logger.error(f'Failed to fetch page {page}: {response["error"]}')
        if not all_coins:
            logger.error('Failed to fetch any coins from CoinGecko API')
            return ResponseHandler.error('Failed to fetch any coins from API')
        logger.info(f'Successfully fetch a total of {len(all_coins)} coins from CoinGeck API')
        return ResponseHandler.success('Fetched coins from API', data=all_coins)
    
    @staticmethod
    @log_function_call(logger)
    def fetch_single_coin_price(api_id, max_retries=5):
        url = f'{CoinGeckoService.BASE_URL}/coins/{api_id}'
        params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'vs_currency': 'usd',
                'order' : 'market_cap_desc',
                'per_page' : 1,
                'page' : 1,
                'sparkline' : 'false',
                'price_change_percentage' : '1h,24h',
                'x_cg_demo_api_key': Config.CG_API_KEY
            }
        for attempt in range(max_retries):
            logger.info(f'Fetching price for coin {api_id} - Attempt {attempt + 1}')
            response = CoinGeckoService._make_request(url, params=params)

            if response['success']:
                logger.info(f'Successfully fetched price data for {api_id}')    
                return ResponseHandler.success(f'Located coin data', data=response['data'])
        
            if response['error'] == 404:
                logger.warning(f'Coin {api_id} not found in CoinGecko API')
                return ResponseHandler.error(f'{api_id} not found')
            
            if response['error'] == 429:
                logger.warning(f'Rate limit hit for {api_id} on attempt {attempt + 1}. Retrying...')
                if attempt == max_retries - 1:
                    logger.error(f'Max retries reached for {api_id}')
                    return ResponseHandler.error(f'{api_id} not found after {max_retries}')
            else:
                logger.error(f'Failed to fetch data for {api_id}: {response["error"]}')
                continue

            time.sleep(4.5 ** attempt)
            
        
        return ResponseHandler.error('No coin found')
    
    @staticmethod
    def _make_request(url, params):
        try:
            logger.debug(f'Sending request to URL: {url}')
            logger.debug(f'With params: {params}')
            response = requests.get(url, params=params, headers=CoinGeckoService._get_headers())
            logger.debug(f'Response status code: {response.status_code}')
            
            if response.status_code == 404:
                logger.warning(f'Resource not found: {url}')
                return ResponseHandler.error(response.status_code)
            response.raise_for_status()
            return ResponseHandler.success('Request successful', data=response.json())
        except requests.exceptions.HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err.response.status_code} {http_err.response.reason} for URL: {http_err.response.url}')
            return ResponseHandler.error(response.status_code)
        except requests.exceptions.RequestException as err:
            logger.error(f'An error occured: {err}', exc_info=True)
            return ResponseHandler.error(f'Request Error: {err}')
        except json.JSONDecodeError as json_err:
            logger.error(f'JSON decode error: {json_err}', exc_info=True)
            return ResponseHandler.error(f'JSON decode error: {json_err}')
        
    @staticmethod
    def _get_headers():
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0: Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }