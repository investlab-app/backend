from modules.investors.models import Asset
from modules.orders.models import Order, MarketOrder
from modules.orders.order_engine.structures import (
    EngineOrder,
    MarketEngineOrder,
    EngineAsset
)

def OrderToEngineOrder(order :Order) -> EngineOrder | None:
    if isinstance(order.detail, MarketOrder):
        return MarketEngineOrder(
            id=str(order.id),
            ticker=order.ticker.ticker,
            investor_id=str(order.investor.id),
            volume=order.detail.volume,
            is_buy=order.detail.is_buy,
            volume_processed=order.detail.volume_processed
        )
    return None

def AssetToEngineAsset(asset :Asset) -> EngineAsset:
    return EngineAsset(
        investor_id=str(asset.investor.id),
        volume=asset.volume,
        ticker=asset.ticker
    )