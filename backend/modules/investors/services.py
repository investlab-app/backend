
from enum import Enum


class InvestorLevel(Enum):
    ROOKIE_TRADER = 0
    STOCK_WATCHER = 250
    ACTIVE_INVESTOR = 1000
    MARKET_TYCOON = 2500

    @classmethod
    def from_exp(cls, exp: int) -> "InvestorLevel":
        for level in sorted(cls, key=lambda l: l.value, reverse=True):
            if exp >= level.value:
                return level
        return cls.ROOKIE_TRADER

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class InvestorsService:
    @staticmethod
    def get_level_from_exp(exp):
        return str(InvestorLevel.from_exp(exp))