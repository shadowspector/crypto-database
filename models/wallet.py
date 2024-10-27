from dataclasses import dataclass

@dataclass
class WalletItem:
    token: str
    price: float
    holdings: float
    value: float
    original_name: str

    def __post_init__(self):
        self.price = float(self.price)
        self.holdings = float(self.holdings)
        self.value = float(self.value)

    def calculate_percent_of_total(self, total_value):
        return (self.value / total_value * 100) if total_value > 0 else 0