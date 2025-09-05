import mimetypes
from collections.abc import Iterable

import requests
from django.core.files.base import ContentFile

from config.settings import POLYGON_SECRET_KEY
from modules.instruments.models import Instrument


class SyncInstrumentsImages:
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

    def sync_instruments_images(self) -> dict[str, int]:
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
