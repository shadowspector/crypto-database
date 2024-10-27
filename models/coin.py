from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Coin:
    Name: str
    CurrentPrice: float
    MarketCap: float
    MarketCapRank: int
    TotalVolume: float
    High24h: float
    Low24h: float
    PriceChange24h: float
    PriceChangePercentage24h: float
    MarketCapChange24h: float
    MarketCapChangePercentage24h: float
    PriceChangePercentage1h: float
    DisplayName: str
    ApiId: str
    AlternateNames: Optional[List[str]] = field(default_factory=list)

    def add_alternate_name(self, name: str):
        if name not in self.AlternateNames:
            self.AlternateNames.append(name)
    
    def to_dict(self):
        return {
            'Name': self.Name,
            'CurrentPrice': self.CurrentPrice,
            'MarketCap': self.MarketCap,
            'MarketCapRank': self.MarketCapRank,
            'TotalVolume': self.TotalVolume,
            'High24h': self.High24h,
            'Low24h': self.Low24h,
            'PriceChange24h': self.PriceChange24h,
            'PriceChangePercentage24h': self.PriceChangePercentage24h,
            'MarketCapChange24h': self.MarketCapChange24h,
            'MarketCapChangePercentage': self.MarketCapChangePercentage24h,
            'PriceChangePercentage1h': self.PriceChangePercentage1h,
            'DisplayName': self.DisplayName,
            'ApiId': self.ApiId,
            'AlternateNames': self.AlternateNames
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
