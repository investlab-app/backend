import uuid

from pydantic import BaseModel, Field

# Lazy import to avoid starting background event loop during Django startup
_live_prices = None

def get_live_prices():
    global _live_prices
    if _live_prices is None:
        from modules.prices.services import LivePrices
        _live_prices = LivePrices()
    return _live_prices

# For backward compatibility
live_prices = type('LivePricesProxy', (), {
    '__getattr__': lambda self, name: getattr(get_live_prices(), name)
})()
