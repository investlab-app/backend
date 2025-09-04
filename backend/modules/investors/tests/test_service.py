import pytest

from modules.investors.models import Investor
from modules.investors.services import ExpPoints, InvestorLevel, InvestorsService


@pytest.mark.parametrize(
    "exp,expected_level",
    [
        (0, InvestorLevel.ROOKIE_TRADER),
        (249, InvestorLevel.ROOKIE_TRADER),
        (250, InvestorLevel.STOCK_WATCHER),
        (999, InvestorLevel.STOCK_WATCHER),
        (1000, InvestorLevel.ACTIVE_INVESTOR),
        (2499, InvestorLevel.ACTIVE_INVESTOR),
        (2500, InvestorLevel.MARKET_TYCOON),
        (9999, InvestorLevel.MARKET_TYCOON),
    ],
)
def test_get_level_from_exp(exp, expected_level):
    level = InvestorLevel.from_exp(exp)
    assert level == expected_level
    assert str(level) == expected_level.name.replace("_", " ").title()


def test_str_representation_of_levels():
    assert str(InvestorLevel.ROOKIE_TRADER) == "Rookie Trader"
    assert str(InvestorLevel.MARKET_TYCOON) == "Market Tycoon"


@pytest.mark.django_db
def test_add_exp_for_transaction():
    investor = Investor.objects.create(clerk_id="user_xyz", exp=0)

    volume = 3
    expected_increase = ExpPoints.TRANSACTION_PER_SHARE.value * volume

    InvestorsService.add_exp_for_transaction(investor.id, volume)  # ty: ignore

    investor.refresh_from_db()
    assert investor.exp == expected_increase  # ty: ignore
