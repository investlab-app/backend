from enum import Enum

from modules.investors.models import Investor


class InvestorLevel(Enum):
    ROOKIE_TRADER = 0
    STOCK_WATCHER = 250
    ACTIVE_INVESTOR = 1000
    MARKET_TYCOON = 2500

    @classmethod
    def from_exp(cls, exp: int) -> "InvestorLevel":
        for level in sorted(cls, key=lambda lvl: lvl.value, reverse=True):
            if exp >= level.value:
                return level
        return cls.ROOKIE_TRADER

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class ExpPoints(Enum):
    TRANSACTION_PER_SHARE = 10
    PROFIT_5_PERCENT = 25


class InvestorsService:
    @staticmethod
    def get_level_from_exp(exp):
        return str(InvestorLevel.from_exp(exp))

    @staticmethod
    def add_exp_for_transaction(investor_id: int, volume: float):
        investor = Investor.objects.get(pk=investor_id)  # ty: ignore
        investor.exp += ExpPoints.TRANSACTION_PER_SHARE.value * volume  # ty: ignore
        investor.save()
