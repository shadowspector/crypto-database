from moralis import evm_api
from config import Config
from utils.response import ResponseHandler
from utils.logging_config import setup_logger, log_function_call

logger = setup_logger(__name__)

class MoralisService:
    @staticmethod
    @log_function_call(logger)
    def get_wallet_balances_and_prices(address, chain):
        params = {
            'chain': chain,
            'exclude_spam': True,
            'address': address
        }

        try:
            logger.info(f'Fetching wallet balances and prices from Moralis for chain: {chain}')
            result = evm_api.wallets.get_wallet_token_balances_price(
                api_key=Config.MORALIS_API_KEY,
                params=params
            )

            if result:
                logger.info(f'Successfully fetched data for {chain}')
                return ResponseHandler.success('Data fetched successfully', data=result)
            else:
                logger.error(f'No data returned for chain {chain}')
                return ResponseHandler.error(f'No data returned for chain {chain}')
        except Exception as e:
            logger.error(f'Error fetching data from Moralis for chain {chain}: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Error fetching data: {str(e)}')
        
   