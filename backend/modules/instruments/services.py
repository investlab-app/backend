from typing import Iterable

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

    def __init__(self, repository: PolygonTickersRepository = None):
        self.repository = repository or PolygonTickersRepository()

    def sync_instruments(self) -> dict[str, int]:
        """Synchronize instruments base on Polygon Tickers."""
        tickers_data = self.repository.list_tickers()
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


class SyncInstrumentsDetailInfoService(UpdateWithMappingMixin):
    BATCH_SIZE = 500
    EDITABLE_FIELDS_MAPPING = {
        "active": "active",
        "cik": "cik",
        "composite_figi": "composite_figi",
        "currency_name": "currency_name",
        "currency_symbol": "currency_symbol",
        "base_currency_symbol": "base_currency_symbol",
        "base_currency_name": "base_currency_name",
        "description": "description",
        "ticker_root": "ticker_root",
        "ticker_suffix": "ticker_suffix",
        "homepage_url": "homepage_url",
        "list_date": "list_date",
        "locale": "locale",
        "market": "market",
        "market_cap": "market_cap",
        "name": "name",
        "phone_number": "phone_number",
        "primary_exchange": "primary_exchange",
        "share_class_figi": "share_class_figi",
        "share_class_shares_outstanding": "share_class_shares_outstanding",
        "sic_code": "sic_code",
        "sic_description": "sic_description",
        "total_employees": "total_employees",
        "type": "type",
        "weighted_shares_outstanding": "weighted_shares_outstanding",
        # Flatten address fields
        "address__address1": "address1",
        "address__address2": "address2",
        "address__city": "city",
        "address__state": "state",
        "address__country": "country",
        "address__postal_code": "postal_code",
        # Flatten branding fields
        "branding__icon_url": "icon_url",
        "branding__logo_url": "logo_url",
    }

    def __init__(
        self,
        instruments: Iterable[Instrument] = None,
        repository: PolygonTickersRepository = None,
    ):
        self.instruments = instruments or Instrument.objects.all()
        self.repository = repository or PolygonTickersRepository()

    def sync_instruments_details(self) -> dict[str, int]:
        """Synchronize instruments details based on Polygon TickerDetails."""
        to_update = []
        no_changes, errors = 0, 0

        for instrument in self.instruments:
            try:
                ticker_details = self.repository.get_ticker_details(instrument.ticker)
            except ValueError:
                errors += 1
                continue

            updated_instrument, updated = self.update_with_mapping(
                instrument, ticker_details
            )
            if updated:
                to_update.append(updated_instrument)
            else:
                no_changes += 1

        Instrument.objects.bulk_update(
            to_update,
            fields=list(self.EDITABLE_FIELDS_MAPPING.values()),
            batch_size=self.BATCH_SIZE,
        )

        return {
            "updated": len(to_update),
            "no_changes": no_changes,
            "errors": errors,
        }
