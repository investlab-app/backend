from modules.investors.models import Asset
from modules.orders.models import MarketOrder, Order, LimitOrder
from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineOrder,
    MarketEngineOrder,
    LimitEngineOrder,
)


def order_to_engine_order(order: Order) -> EngineOrder | None:
    if isinstance(order.detail, MarketOrder):
        return MarketEngineOrder(
            id=order.id,
            ticker=order.ticker.ticker,  # ty: ignore[possibly-unbound-attribute]
            investor_id=str(order.investor.id),  # ty: ignore[possibly-unbound-attribute]
            volume=order.detail.volume,  # ty: ignore[possibly-unbound-attribute]
            is_buy=order.detail.is_buy,  # ty: ignore[possibly-unbound-attribute]
            volume_processed=order.detail.volume_processed,  # ty: ignore
        )
    if isinstance(order.detail, LimitOrder):
        return LimitEngineOrder(
            id=order.id,
            ticker=order.ticker.ticker,  # ty: ignore[possibly-unbound-attribute]
            investor_id=str(order.investor.id),  # ty: ignore[possibly-unbound-attribute]
            volume=order.detail.volume,  # ty: ignore[possibly-unbound-attribute]
            is_buy=order.detail.is_buy,  # ty: ignore[possibly-unbound-attribute]
            limit_price=order.detail.limit_price,  # ty: ignore
            volume_processed=order.detail.volume_processed,  # ty: ignore
        )
    return None


def asset_to_engine_asset(asset: Asset) -> EngineAsset:
    return EngineAsset(
        investor_id=str(asset.investor.id),  # ty: ignore[possibly-unbound-attribute]
        volume=asset.volume,
        ticker=asset.ticker.ticker,  # ty: ignore[possibly-unbound-attribute]
    )
