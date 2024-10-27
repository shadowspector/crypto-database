from services.database import DatabaseService
from services.coin_price_service import CoinPriceService
from services.position_metadata_service import PositionMetadataService
from utils.logging_config import setup_logger, log_function_call
from utils.response import ResponseHandler
from typing import Optional
from dataclasses import dataclass

logger = setup_logger(__name__)

@dataclass
class StakedPosition:
    pool: str
    token: str  # Represents token's DisplayName
    price: float
    holdings: float
    value: float
    deposited_amount: float
    project: str
    chain: str
    
    def calculate_percent_of_total(self, total_value):
        """Calculate what percentage of the total portfolio this position represents"""
        return (self.value / total_value * 100) if total_value > 0 else 0
    

class StakingService:
    @staticmethod
    @log_function_call(logger)
    def get_staked_positions(sort_by='Value', order='desc'):
        """
        Get all staked positions

        Args:
            sort_by: column to sort
            order: asc or desc
        
        Returns:
            dict: Response with list of staked positions
        """

        try:
            valid_columns = {'Pool', 'Token', 'Price', 'Holdings', 'Value',
                              'DepositedAmount', 'Project', 'Chain'}
            
            if sort_by not in valid_columns:
                sort_by = 'Value'

            query = f'''
                SELECT Pool, Token, Price, Holdings, Value,
                       DepositedAmount, Project, Chain
                FROM Staking
                ORDER BY {sort_by} {"DESC" if order == "desc" else "ASC"}
            '''

            result = DatabaseService.execute_query(query)
            positions = []

            for row in result:
                position = StakedPosition(
                    pool = row[0],
                    token = row[1], 
                    price = row[2],
                    holdings = row[3],
                    value = row[4],
                    deposited_amount = row[5],
                    project = row[6],
                    chain = row[7]
                )
                positions.append(position)
            
            return ResponseHandler.success('Retrieved staked positions', data=positions)
        except Exception as e:
            logger.error(f'Error retrieving staked positions: {str(e)}')
            return ResponseHandler.error(f'Failed to retrieve staked positions: {str(e)}')
        
    
    @staticmethod
    @log_function_call(logger)
    def add_staked_position(pool, token, holdings, deposited_amount, project, chain):
        """
        Add a new staked position and create associated metadata.

        Args:
            pool: Unique identifier for the staking position
            token: name of token (must exist in CoinPrices)
            price: price of token
            holdings: number of tokens
            project: project where tokens are staked
            chain: chain project is on

        Returns:
            Response Handler: shows success or failure
        """

        try:
            # Verify token exists and get current price
            coin_result = CoinPriceService.find_coin_by_name(token)
            if not coin_result['succes']:
                return ResponseHandler.error(f'Token {token} not found in database')
            
            name = coin_result['data'][0]
            coin_info_result = CoinPriceService.find_token(name)
            if not coin_info_result:
                return ResponseHandler.error(f'Price not found for token {token}')
            coin_info = coin_info_result['data']
            coin_name = coin_info[1]
            price = coin_info[2]

            query = '''
                INSERT INTO Staking (Pool, Token, Price, Holdings, DepositedAmount, Project, Chain)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            DatabaseService.execute_query(query, (pool, coin_name, price, holdings, deposited_amount, project, chain))

            metadata_result = PositionMetadataService.create_or_update_metadata(
                position_type='Staking',
                position_id=pool,
                protocol=project,
                chain=chain
            )

            if not metadata_result['success']:
                raise Exception(f'Failed to create position metadata: {metadata_result['error']}')

            logger.info(f'Added staked position for {pool} with metadata')
            return ResponseHandler.success('Staked position added successfully')
        except Exception as e:
            logger.error(f'Error adding staked position for {token}: {str(e)}')
            return ResponseHandler.error(f'Failed to add staked position: {str(e)}')
        
    @staticmethod
    @log_function_call(logger)
    def update_staked_postion(current_pool, new_pool, holdings, deposited_amount=None):
        """
        Update an existing staked position.

        Args:
            token: name of token (must exist in staking)
            holdings: updated holding count
            deposited_amount: optional update of deposited amount
        
        Returns:
            Response Handler: Success or Failure
        """
        try:
            # Get current price
            token_result = DatabaseService.execute_query(
                'SELECT Token FROM Staking WHERE Pool = ?',
                (current_pool,)
            )
            if not token_result:
                return ResponseHandler.error(f'Pool {current_pool} not found')
            token = token_result[0][0]
            price_result = CoinPriceService.find_token(token)

            if not price_result:
                return ResponseHandler.error(f'Price not found for token {token}')
            
            price = price_result['data'][2]

            # If pool name is changing, verify new name doesn't exist
            if current_pool != new_pool:
                existing = DatabaseService.execute_query(
                    'SELECT 1 FROM Staking WHERE Pool = ? AND Pool != ?',
                    (new_pool, current_pool)
                )
                if existing:
                    return ResponseHandler.error(f'Pool name {new_pool} already exists')
                
            if deposited_amount is not None:
                query = '''
                    UPDATE Staking
                    SET Pool = ?, Holdings = ?, Price = ?, DepositedAmount = ?
                    WHERE Token = ?
                '''
                params = (new_pool, holdings, price, deposited_amount, token)
            else:
                query = '''
                    UPDATE Staking
                    SET Pool = ?, Holdings = ?, Price = ?
                    WHERE Token = ?
                '''
                params = (new_pool, holdings, price, token)
            
            DatabaseService.execute_query(query, params)

            logger.info(f'Updated stake positon for {token}')
            return ResponseHandler.success(f'Staked position updated successfully')
        except Exception as e:
            logger.error(f'Error updating staked position for {token}: {str(e)}')
            return ResponseHandler.error(f'Failed to update staked position: {str(e)}')
        
    
    @staticmethod
    @log_function_call(logger)
    def calculate_total_staking_value():
        """Calculate total value of all stked positions."""
        query = 'SELECT COALESCE(SUM(Value), 0) FROM Staking'
        result = DatabaseService.execute_query(query)
        return result[0][0] if result else 0

