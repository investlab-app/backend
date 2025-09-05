from modules.core.mixins import CreateWithMappingMixin, UpdateWithMappingMixin
from modules.instruments.models import Instrument
from modules.instruments.repositories import PolygonTickersRepository


class SyncInstrumentsBaseInfoService(CreateWithMappingMixin, UpdateWithMappingMixin):
    BATCH_SIZE = 500
    EDITABLE_FIELDS_MAPPING = {
        "active": "active",
        "cik": "cik",
        "composite_figi": "composite_figi",
        "currency_name": "currency_name",
        "currency_symbol": "currency_symbol",
        "base_currency_symbol": "base_currency_symbol",
        "base_currency_name": "base_currency_name",
        "locale": "locale",
        "market": "market",
        "name": "name",
        "primary_exchange": "primary_exchange",
        "share_class_figi": "share_class_figi",
        "type": "type",
    }
    CREATABLE_FIELDS_MAPPING = {
        "ticker": "ticker",
        **EDITABLE_FIELDS_MAPPING,
    }

    def __init__(self, repository: PolygonTickersRepository = None):  # type: ignore
        self.repository = repository or PolygonTickersRepository()

    def sync_instruments(self) -> dict[str, int]:
        """Synchronize instruments based on Polygon Tickers."""
        tickers_data = self.repository.list_tickers()
        if not tickers_data:
            raise RuntimeError("Failed to fetch tickers from Polygon API.")

        to_create, to_update = [], []
        no_changes = 0

        for ticker_data in tickers_data:
            if instrument := Instrument.objects.filter(
                ticker=ticker_data.ticker
            ).first():
                # Update existing instrument
                updated_instrument, updated = self.update_with_mapping(
                    instrument, ticker_data
                )
                if updated:
                    to_update.append(updated_instrument)
                else:
                    no_changes += 1
            else:
                # Create new ticker
                new_instrument = self.create_with_mapping(ticker_data, Instrument)
                to_create.append(new_instrument)

        Instrument.objects.bulk_create(to_create, batch_size=self.BATCH_SIZE)
        Instrument.objects.bulk_update(
            to_update,
            fields=list(self.EDITABLE_FIELDS_MAPPING.values()),
            batch_size=self.BATCH_SIZE,
        )

        return {
            "created": len(to_create),
            "updated": len(to_update),
            "no_changes": no_changes,
        }
