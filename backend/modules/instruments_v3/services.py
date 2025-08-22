from modules.instruments_v3.models import Ticker
from modules.instruments_v3.repositories import PolygonInstrumentsRepository
from polygon.rest.models.tickers import Ticker as TickerData


class SyncTickersService:
    BATCH_SIZE = 500
    EDITABLE_FIELDS_MAPPING = {
        "active": "active",
        "cik": "cik",
        "composite_figi": "composite_figi",
        "currency_name": "currency_name",
        "currency_symbol": "currency_symbol",
        "base_currency_symbol": "base_currency_symbol",
        "base_currency_name": "base_currency_name",
        "delisted_utc": "delisted_utc",
        "last_updated_utc": "last_updated_utc",
        "locale": "locale",
        "market": "market",
        "name": "name",
        "primary_exchange": "primary_exchange",
        "share_class_figi": "share_class_figi",
        "type": "type",
        "source_feed": "source_feed",
    }
    CREATABLE_FIELDS_MAPPING = {
        "ticker": "ticker",
        **EDITABLE_FIELDS_MAPPING,
    }

    def __init__(
        self, repository: PolygonInstrumentsRepository = None
    ):
        self.repository = repository or PolygonInstrumentsRepository()

    def _update_ticker(self, ticker: Ticker, ticker_data: TickerData) -> tuple[Ticker, bool]:
        """Update existing ticker with new data."""
        updated = False
        for data_field, model_field in self.EDITABLE_FIELDS_MAPPING.items():
            new_value = getattr(ticker_data, data_field)
            if getattr(ticker, model_field) != new_value:
                setattr(ticker, model_field, new_value)
                updated = True
        return ticker, updated

    def _create_ticker(self, ticker_data: TickerData) -> Ticker:
        """Create a new ticker from the provided data."""
        return Ticker(
            **{
                model_field: getattr(ticker_data, data_field)
                for data_field, model_field in self.CREATABLE_FIELDS_MAPPING.items()
            }
        )

    def sync_tickers(self) -> dict[str, int]:
        """Synchronize tickers from Polygon API."""
        tickers_data = self.repository.list_tickers()
        to_create, to_update = [], []
        no_changes = 0

        for ticker_data in tickers_data:
            if ticker := Ticker.objects.filter(ticker=ticker_data.ticker).first():
                # Update existing ticker
                updated_ticker, updated = self._update_ticker(ticker, ticker_data)
                if updated:
                    to_update.append(updated_ticker)
                else:
                    no_changes += 1
            else:
                # Create new ticker
                new_ticker = self._create_ticker(ticker_data)
                to_create.append(new_ticker)

        Ticker.objects.bulk_create(to_create, batch_size=self.BATCH_SIZE)
        Ticker.objects.bulk_update(
            to_update,
            fields=list(self.EDITABLE_FIELDS_MAPPING.values()),
            batch_size=self.BATCH_SIZE
        )

        return {
            "created": len(to_create),
            "updated": len(to_update),
            "no_changes": no_changes,
        }
