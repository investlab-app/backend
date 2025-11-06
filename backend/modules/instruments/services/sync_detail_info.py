from collections.abc import Iterable

from polygon.rest.models.tickers import TickerDetails

from modules.core.mixins import UpdateWithMappingMixin
from modules.instruments.models import Instrument
from modules.instruments.repositories import PolygonTickersRepository
from modules.instruments.services.translation_service import TranslationService


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
        "description_pl": "description_pl",
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
        "branding__icon_url": "icon_polygon_url",
        "branding__logo_url": "logo_polygon_url",
    }

    def __init__(
        self,
        instruments: Iterable[Instrument] | None = None,
        repository: PolygonTickersRepository | None = None,
        translation_service: TranslationService | None = None,
    ):
        self.instruments = instruments or Instrument.objects.all()
        self.repository = repository or PolygonTickersRepository()
        self.translation_service = translation_service or TranslationService()

    def _translate_description_if_needed(
        self,
        instrument: Instrument,
        ticker_details: TickerDetails,
        *,
        update: bool = True,
    ) -> tuple[Instrument, bool, int]:
        """
        Translate description to Polish if needed.
        Returns updated instrument, whether it was
        updated, and number of translation errors.

        Args:
            instrument (Instrument): The instrument to update.
            ticker_details (TickerDetails): The ticker details from Polygon.
            update (bool): Whether to perform the update.

        Returns:
            tuple[Instrument, bool, int]:
            Updated instrument, update status, translation error count.
        """
        translation_errors = 0
        updated = False
        new_description = ticker_details.description

        if update and new_description:
            try:
                polish_translation = self.translation_service.translate_to_polish(
                    new_description
                )
                if polish_translation:
                    instrument.description_pl = polish_translation
                    updated = True
                else:
                    translation_errors += 1

            except Exception:
                translation_errors += 1

        return instrument, updated, translation_errors

    def sync_instruments_details(self) -> dict[str, int]:
        """Synchronize instruments details based on Polygon TickerDetails."""
        to_update = []
        no_changes, errors, translation_errors = 0, 0, 0

        for instrument in self.instruments:
            ticker_details = self.repository.get_ticker_details(instrument.ticker)
            if not ticker_details:
                errors += 1
                continue

            old_description = instrument.description
            new_description = ticker_details.description
            update_description = old_description != new_description

            updated_instrument, updated = self.update_with_mapping(
                instrument, ticker_details
            )

            (
                updated_instrument,
                translation_updated,
                translation_error_count,
            ) = self._translate_description_if_needed(
                updated_instrument, ticker_details, update=update_description
            )

            translation_errors += translation_error_count
            if translation_updated:
                updated = True

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
            "translation_errors": translation_errors,
        }
