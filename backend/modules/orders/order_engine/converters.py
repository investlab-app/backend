from modules.investors.models import Asset
from modules.orders.models import MarketOrder, Order
from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineOrder,
    MarketEngineOrder,
)


def order_to_engine_order(order: Order) -> EngineOrder | None:
    if isinstance(order.detail, MarketOrder):
        return MarketEngineOrder(
            id=order.id,
            ticker=order.ticker.ticker,
            investor_id=order.investor.id,
            volume=order.detail.volume,
            is_buy=order.detail.is_buy,
            volume_processed=order.detail.volume_processed,
        )
    return None


def asset_to_engine_asset(asset: Asset) -> EngineAsset:
    return EngineAsset(
        investor_id=asset.investor.id, volume=asset.volume, ticker=asset.ticker.ticker
    )
