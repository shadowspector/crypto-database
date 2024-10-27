from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from services.database import DatabaseService
from utils.logging_config import setup_logger, log_function_call
from utils.response import ResponseHandler

logger = setup_logger(__name__)

@dataclass
class PositionMetadata:
    position_type: str
    position_id: str
    protocol: Optional[str] = None
    chain: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None

class PositionMetadataService:
    VALID_POSITION_TYPES = {
        'Wallet', 'Staking', 'Farming',
        'LeveragedFarming', 'LendingBorrowing'

    }

    @staticmethod
    @log_function_call(logger)
    def create_or_update_metadata(position_type, position_id, protocol=None, chain=None):
        """
        Create or update position metadata

        Args:
            position_type: Type (Must be in VALID_POSITION_TYPES)
            position_id: Id for the position in its table
            protocol: optional protocol name
            chain: optional chain name
        
        Returns:
            ResponseHandler with success/error message
        """

        try:
            if position_type not in PositionMetadataService.VALID_POSITION_TYPES:
                return ResponseHandler.error(f'Invalid Position type: {position_type}')
            
            query = '''
                INSERT INTO PositionMetadata (position_type, position_id, protocol, chain)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (position_type, position_id) DO UPDATE SET
                    protocol = excluded.protocol,
                    chain = excluded.chain,
                    updated_at = CURRENT_TIMESTAMP
            '''
            DatabaseService.execute_query(query, (position_type, position_id, protocol, chain))
            return ResponseHandler.success('Position metadata updated successfully')
        except Exception as e:
            logger.error(f'Error updating positon metadata: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Failed to update position metadata: {str(e)}')
        
    
    @staticmethod
    @log_function_call(logger)
    def get_chain_distribution():
        """
        Get distribution of value across different chains

        Returns:
            ResponseHandler
        """
        try:
            query = '''
                SELECT
                    pm.chain,
                    COUNT(DISTINCT pm.position_id) as position_count,
                    COUNT(DISTINCT pm.position_type) as type_count,
                FROM PositionMetadata pm
                WHERE pm.chain IS NOT NULL
                GROUP BY pm.chain
                ORDER BY position_count DESC
            '''
            result = DatabaseService.execute_query(query)

            distribution = [
                {
                    'chain': row[0],
                    'position_count': row[1],
                    'type_count': row[2]
                }
                for row in result
            ]

            return ResponseHandler.success('Chain distribution retrieved', data=distribution)
        except Exception as e:
            logger.error(f'Error getting chain distribution: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Failed to get chain distribution: {str(e)}')
        
    @staticmethod
    @log_function_call(logger)
    def get_protocol_distribution():
        """
        Get distribution of value across different protocols.

        Returns:
            ResponseHandler containing procotol distribution data
        """
        try:
            query = '''
                SELECT
                    pm.protocol,
                    COUNT(DISTINCT pm.position_id) as position_count,
                    COUNT(DISTINCT pm.position_type) as type_count
                FROM PositionMetadata pm
                WHERE pm.protocol IS NOT NULL
                GROUP BY pm.protocol
                ORDER BY position_count DESC

            '''
            result = DatabaseService.execute_query(query)
            distribution = [
                {
                    'protocol': row[0],
                    'position_count': row[1],
                    'type_count': row[2]
                }
                for row in result
            ]

            return ResponseHandler.success('Protocol distribution retrieved', data=distribution)
        except Exception as e:
            logger.error(f'Error getting protocol distribution: {str(e)}', exc_info=True)
            return ResponseHandler.error(f'Failed to get protocol distribution: {str(e)}')
                

