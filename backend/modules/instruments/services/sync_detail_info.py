import logging
from collections.abc import Iterable

from modules.core.mixins import UpdateWithMappingMixin
from modules.instruments.models import Instrument
from modules.instruments.repositories import PolygonTickersRepository
from modules.instruments.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


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

    def sync_instruments_details(self) -> dict[str, int]:
        """Synchronize instruments details based on Polygon TickerDetails."""
        to_update = []
        no_changes, errors, translation_errors = 0, 0, 0

        for instrument in self.instruments[:10]:
            ticker_details = self.repository.get_ticker_details(instrument.ticker)
            if not ticker_details:
                errors += 1
                continue

            old_description = instrument.description
            old_description_pl = instrument.description_pl
            new_description = getattr(ticker_details, "description", None)
            is_description_updated = old_description != new_description

            updated_instrument, updated = self.update_with_mapping(
                instrument, ticker_details
            )

            if not old_description_pl and is_description_updated and new_description:
                try:
                    polish_translation = self.translation_service.translate_to_polish(
                        new_description
                    )

                    if polish_translation:
                        updated_instrument.description_pl = polish_translation
                        updated = True
                        logger.info(
                            "Successfully translated description for %s",
                            instrument.ticker,
                        )
                    else:
                        logger.warning(
                            "Failed to translate description for %s", instrument.ticker
                        )
                        translation_errors += 1

                except Exception as e:
                    logger.error("Translation error for %s: %s", instrument.ticker, e)
                    translation_errors += 1

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
