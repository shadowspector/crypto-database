from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class Position:
    id: str
    protocol_id: str
    position_type: str
    total_value: Decimal
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_new(self) -> bool:
        return self.created_at is None
    
    def validate_type(self) -> bool:
        valid_types = {'wallet', 'staking', 'farming', 'leveraged', 'lending', 'borrowing'}
        return self.position_type in valid_types
    
@dataclass
class WalletPosition:
    """Represents a wallet position with its core position data"""
    position: Position
    coin_id: str
    amount: Decimal
    price: Decimal


    @property
    def value(self) -> Decimal:
        """Calculate position value - matches DB generated column"""
        return self.amount * self.price
    
    @classmethod
    def create_new(cls, coin_id: str, amount: Decimal, price: Decimal) -> 'WalletPosition':
        """Factory method to create a new wallet position"""
        position = Position(
            id=f'wallet_{coin_id}',
            protocol_id ='default',
            position_type = 'wallet',
            total_value=amount * price
        )
        return cls(position=position, coin_id=coin_id, amount=amount, price=price)
