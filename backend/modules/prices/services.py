from dataclasses import asdict
from datetime import datetime
from http.client import HTTPResponse
from typing import Any

from django.shortcuts import get_object_or_404

from config.clients import polygon_client
from config.logging import get_logger
from config.settings import POLYGON_ASSET_TYPE
from modules.instruments.models import Instrument
from modules.prices.exceptions import PayloadTooLarge
from modules.prices.serializers import PriceSerializer

logger = get_logger(__name__)


class PricesV2Service:
    @staticmethod
    def get_ohlc(
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        interval_multiplier: int,
    ):
        get_object_or_404(Instrument, ticker=ticker.upper())
        aggs = polygon_client.list_aggs(
            ticker.upper(), interval_multiplier, interval.lower(), start_date, end_date
        )
        return PricesV2Service._aggs_to_json(aggs, max_aggs=10_000)

    @staticmethod
    def _aggs_to_json(aggs, max_aggs):
        bars = []
        for a in aggs:
            bars.append(PricesV2Service._agg_to_json(a))
            if len(bars) > max_aggs:
                raise PayloadTooLarge
        return bars

    @staticmethod
    def _agg_to_json(agg):
        data = asdict(agg)
        data["timestamp"] = datetime.fromtimestamp(data["timestamp"] / 1000)
        return data

    @staticmethod
    def get_price_info(ticker: str):
        ticker_upper = ticker.upper()
        get_object_or_404(Instrument, ticker=ticker_upper)

        ticker_snapshot = polygon_client.get_snapshot_ticker(
            market_type=POLYGON_ASSET_TYPE, ticker=ticker_upper
        )

        if isinstance(ticker_snapshot, HTTPResponse):
            raise ValueError(
                f"HTTP error {ticker_snapshot.status}: "
                f"{ticker_snapshot.reason} - {ticker_snapshot.msg}"
            )

        if not ticker_snapshot.min:
            raise ValueError(f"No minute data found for ticker {ticker_upper}")

        if not ticker_snapshot.day:
            raise ValueError(f"No daily summary found for ticker {ticker_upper}")

        if not ticker_snapshot.todays_change:
            raise ValueError(f"No today's change found for ticker {ticker_upper}")

        if not ticker_snapshot.todays_change_percent:
            raise ValueError(
                f"No today's change percentage found for ticker {ticker_upper}"
            )

        if not ticker_snapshot.updated:
            raise ValueError(
                f"No last updated timestamp found for ticker {ticker_upper}"
            )

        return {
            "current_price": ticker_snapshot.min.close,
            "daily_summary": {
                "open": ticker_snapshot.day.open,
                "high": ticker_snapshot.day.high,
                "low": ticker_snapshot.day.low,
                "close": ticker_snapshot.day.close,
                "volume": ticker_snapshot.day.volume,
                "volume_weighted_average_price": ticker_snapshot.day.vwap,
            },
            "todays_change": ticker_snapshot.todays_change,
            "todays_change_percent": ticker_snapshot.todays_change_percent,
            "last_updated": ticker_snapshot.updated,
        }

    @staticmethod
    def get_full_market_snapshot(
        *, tickers: list[str] | None = None, include_otc: bool = False
    ) -> dict[str, dict]:
        """
        Fetch a snapshot for all (or selected) tickers and return a mapping of
        ticker -> price info compatible with
        PriceInfoResponseSerializer.sanitize_output.
        """
        # polygon RESTClient get_snapshot_all requires market type string (e.g.
        # 'stocks')
        snapshots = polygon_client.get_snapshot_all(
            POLYGON_ASSET_TYPE,
            tickers=tickers,
            include_otc=include_otc,
        )

        result: dict[str, dict] = {}
        for snap in snapshots:
            try:
                # Extract with getattr to satisfy static analysis
                ticker: Any = getattr(snap, "ticker", None)
                m: Any = getattr(snap, "min", None)
                d: Any = getattr(snap, "day", None)
                todays_change: Any = getattr(snap, "todays_change", None)
                todays_change_percent: Any = getattr(
                    snap, "todays_change_percent", None
                )
                updated: Any = getattr(snap, "updated", None)

                if (
                    not ticker
                    or m is None
                    or d is None
                    or todays_change is None
                    or todays_change_percent is None
                    or not updated
                ):
                    continue

                current_price: Any = getattr(m, "close", None)
                open_: Any = getattr(d, "open", None)
                high: Any = getattr(d, "high", None)
                low: Any = getattr(d, "low", None)
                close: Any = getattr(d, "close", None)
                volume: Any = getattr(d, "volume", None)
                vwap: Any = getattr(d, "vwap", None)

                if (
                    current_price is None
                    or open_ is None
                    or high is None
                    or low is None
                    or close is None
                    or volume is None
                    or vwap is None
                ):
                    continue

                data = {
                    "current_price": current_price,
                    "daily_summary": {
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                        "volume_weighted_average_price": vwap,
                    },
                    "todays_change": todays_change,
                    "todays_change_percent": todays_change_percent,
                    "last_updated": updated,
                }

                sanitized = PriceSerializer.sanitize_output(data)
                # Validate and store normalized payload
                serializer = PriceSerializer(data=sanitized)
                serializer.is_valid(raise_exception=True)
                result[str(ticker).upper()] = serializer.validated_data
            except Exception:
                # Skip problematic entries rather than fail the entire snapshot
                continue
        return result
