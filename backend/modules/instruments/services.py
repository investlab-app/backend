import mimetypes
from collections.abc import Iterable

import requests
from django.core.files.base import ContentFile

from config.settings import POLYGON_SECRET_KEY
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
        "branding__icon_url": "icon_polygon_url",
        "branding__logo_url": "logo_polygon_url",
    }

    def __init__(
        self,
        instruments: Iterable[Instrument] = None,  # type: ignore
        repository: PolygonTickersRepository = None,  # type: ignore
    ):
        self.instruments = instruments or Instrument.objects.all()
        self.repository = repository or PolygonTickersRepository()

    def sync_instruments_details(self) -> dict[str, int]:
        """Synchronize instruments details based on Polygon TickerDetails."""
        to_update = []
        no_changes, errors = 0, 0

        for instrument in self.instruments:
            ticker_details = self.repository.get_ticker_details(instrument.ticker)
            if not ticker_details:
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


class SyncInstrumentImages:
    def __init__(
        self,
        instruments: Iterable[Instrument] = None,  # type: ignore
        polygon_api_key: str = POLYGON_SECRET_KEY,  # type: ignore
    ):
        self.instruments = instruments or Instrument.objects.all()
        self.polygon_api_key = polygon_api_key

    def get_image(self, url: str) -> tuple[bytes, str] | None:
        """Fetch image and its extension from URL."""
        response = requests.get(url, params={"apiKey": self.polygon_api_key})
        if response.status_code != 200:
            return None

        image_bytes = response.content
        content_type = response.headers.get("Content-Type")
        if content_type:
            extension = mimetypes.guess_extension(content_type)
            # Some MIME types might return uncommon extensions
            if extension == ".jpe":
                extension = ".jpg"
        else:
            extension = None

        if image_bytes and extension:
            return image_bytes, extension
        return None

    def sync_instrument_images(self) -> dict[str, int]:
        """Synchronize instrument images (icon and logo) from Polygon."""
        to_update = []
        no_logo, errors = 0, 0

        for instrument in self.instruments:
            updated = False
            if instrument.icon_polygon_url:
                icon_data, icon_ext = self.get_image(instrument.icon_polygon_url)
                if icon_data and icon_ext:
                    instrument.icon.save(
                        f"{instrument.ticker}_icon{icon_ext}",
                        content=ContentFile(icon_data),
                        save=False,
                    )
                    updated = True

            if instrument.logo_polygon_url:
                logo_data, logo_ext = self.get_image(instrument.logo_polygon_url)
                if logo_data and logo_ext:
                    instrument.logo.save(
                        f"{instrument.ticker}_logo{logo_ext}",
                        content=ContentFile(logo_data),
                        save=False,
                    )
                    updated = True

            if updated:
                to_update.append(instrument)
            else:
                no_logo += 1

        Instrument.objects.bulk_update(
            to_update,
            fields=["icon", "logo"],
            batch_size=500,
        )

        return {
            "updated": len(to_update),
            "no_logo": no_logo,
            "errors": errors,
        }
