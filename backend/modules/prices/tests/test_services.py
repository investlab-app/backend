import contextlib
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from channels.db import database_sync_to_async

from modules.instruments.models import Instrument
from modules.notifications.models import NotificationConfig
from modules.notifications.services import (
    EmailPayload,
    PushPayload,
    WebSocketPayload,
)
from modules.prices.models import PriceAlert
from modules.prices.services import PriceAlertHandler, PriceNotificationService


@pytest.fixture
def mock_notification_service():
    """Mock notification service"""
    mock = AsyncMock()
    mock.send_email_notification = AsyncMock()
    mock.send_push_notifications = AsyncMock()
    mock.send_websocket_notifications = AsyncMock()
    return mock


@pytest.mark.django_db
class TestPriceAlertHandler:
    """Tests for PriceAlertHandler"""

    @pytest.fixture(autouse=True)
    def setup(self, mock_notification_service):
        self.handler = PriceAlertHandler(notification_service=mock_notification_service)
        self.mock_notification_service = mock_notification_service

    @pytest.mark.asyncio
    async def test_handle__no_alerts__returns_without_processing(self):
        """Test handle with no matching alerts"""
        prices = {"AAPL": {"close": 150.0}}

        await self.handler.handle(prices=prices)

        self.mock_notification_service.send_email_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle__alert_below_triggered__processes_notification(
        self, investor_factory, instruments_factory
    ):
        """Test handle with below threshold alert triggered"""

        def setup():
            investor = investor_factory()
            instrument = instruments_factory()
            notification_config = NotificationConfig.objects.create(
                is_email=True, is_push=False, is_websocket=False, is_active=True
            )

            PriceAlert.objects.create(
                investor=investor,
                instrument=instrument,
                notification_config=notification_config,
                threshold_type="below",
                threshold_value=Decimal("150.00"),
            )
            return instrument.ticker

        ticker = await database_sync_to_async(setup)()
        prices = {ticker: {"close": 145.0}}

        await self.handler.handle(prices=prices)

        self.mock_notification_service.send_email_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle__alert_above_triggered__processes_notification(
        self, investor_factory, instruments_factory
    ):
        """Test handle with above threshold alert triggered"""

        def setup():
            investor = investor_factory()
            instrument = instruments_factory()
            notification_config = NotificationConfig.objects.create(
                is_email=True, is_push=False, is_websocket=False, is_active=True
            )

            PriceAlert.objects.create(
                investor=investor,
                instrument=instrument,
                notification_config=notification_config,
                threshold_type="above",
                threshold_value=Decimal("150.00"),
            )
            return instrument.ticker

        ticker = await database_sync_to_async(setup)()
        prices = {ticker: {"close": 155.0}}

        await self.handler.handle(prices=prices)

        self.mock_notification_service.send_email_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle__multiple_alerts__processes_all(
        self, investor_factory, instruments_factory
    ):
        """Test handle with multiple alerts"""

        def setup():
            investor = investor_factory()
            instrument1 = instruments_factory()
            instrument2 = instruments_factory()
            notification_config = NotificationConfig.objects.create(
                is_email=True, is_push=False, is_websocket=False, is_active=True
            )

            PriceAlert.objects.create(
                investor=investor,
                instrument=instrument1,
                notification_config=notification_config,
                threshold_type="below",
                threshold_value=Decimal("150.00"),
            )

            PriceAlert.objects.create(
                investor=investor,
                instrument=instrument2,
                notification_config=notification_config,
                threshold_type="above",
                threshold_value=Decimal("200.00"),
            )
            return instrument1.ticker, instrument2.ticker

        ticker1, ticker2 = await database_sync_to_async(setup)()
        prices = {
            ticker1: {"close": 145.0},
            ticker2: {"close": 210.0},
        }

        await self.handler.handle(prices=prices)

        assert self.mock_notification_service.send_email_notification.call_count == 2

    def test_get_email_payload__english__returns_english_message(
        self, investor_factory, instruments_factory
    ):
        """Test email payload generation in English"""
        investor = investor_factory()
        instrument = instruments_factory()
        notification_config = NotificationConfig.objects.create()

        alert = PriceAlert.objects.create(
            investor=investor,
            instrument=instrument,
            notification_config=notification_config,
            threshold_type="above",
            threshold_value=Decimal("150.00"),
        )

        payload = self.handler.get_email_payload(
            language="en",
            ticker="AAPL",
            current_price=155.0,
            notification=alert,
        )

        assert isinstance(payload, EmailPayload)
        assert payload.subject == "Price Alert"
        assert "AAPL" in payload.body
        assert "155.0" in payload.body

    def test_get_email_payload__polish__returns_polish_message(
        self, investor_factory, instruments_factory
    ):
        """Test email payload generation in Polish"""
        investor = investor_factory()
        instrument = instruments_factory()
        notification_config = NotificationConfig.objects.create()

        alert = PriceAlert.objects.create(
            investor=investor,
            instrument=instrument,
            notification_config=notification_config,
            threshold_type="above",
            threshold_value=Decimal("150.00"),
        )

        payload = self.handler.get_email_payload(
            language="pl",
            ticker="AAPL",
            current_price=155.0,
            notification=alert,
        )

        assert isinstance(payload, EmailPayload)
        assert payload.subject == "Alert cenowy"

    def test_get_push_payload__english__returns_english_message(
        self, investor_factory, instruments_factory
    ):
        """Test push payload generation in English"""
        investor = investor_factory()
        instrument = instruments_factory()
        notification_config = NotificationConfig.objects.create()

        alert = PriceAlert.objects.create(
            investor=investor,
            instrument=instrument,
            notification_config=notification_config,
            threshold_type="below",
            threshold_value=Decimal("150.00"),
        )

        payload = self.handler.get_push_payload(
            language="en",
            ticker="AAPL",
            current_price=145.0,
            notification=alert,
        )

        assert isinstance(payload, PushPayload)
        assert payload.title == "Price Alert"
        assert "AAPL" in payload.body

    def test_get_websocket_payload__returns_websocket_message(
        self, investor_factory, instruments_factory
    ):
        """Test WebSocket payload generation"""
        investor = investor_factory()
        instrument = instruments_factory()
        notification_config = NotificationConfig.objects.create()

        alert = PriceAlert.objects.create(
            investor=investor,
            instrument=instrument,
            notification_config=notification_config,
            threshold_type="above",
            threshold_value=Decimal("150.00"),
        )

        payload = self.handler.get_websocket_payload(
            language="en",
            ticker="AAPL",
            current_price=155.0,
            notification=alert,
        )

        assert isinstance(payload, WebSocketPayload)
        assert payload.message["type"] == "price_alert"
        assert payload.message["title"] == "Price Alert"


@pytest.mark.django_db
class TestPriceNotificationService:
    """Tests for PriceNotificationService"""

    @pytest.fixture(autouse=True)
    def setup(self, mock_notification_service):
        self.mock_handler = AsyncMock()
        self.service = PriceNotificationService(price_alert_handler=self.mock_handler)

    @pytest.mark.asyncio
    async def test_listen_prices__initializes_correctly(self):
        """Test listen_prices initializes channel layer correctly"""
        with patch("modules.prices.services.get_channel_layer") as mock_layer:
            mock_layer_instance = AsyncMock()
            mock_layer.return_value = mock_layer_instance

            # Set up mock to stop after first iteration to avoid infinite loop
            mock_layer_instance.receive.side_effect = KeyboardInterrupt()
            mock_layer_instance.new_channel.return_value = "test_channel"

            with contextlib.suppress(KeyboardInterrupt):
                await self.service.listen_prices()

            mock_layer_instance.new_channel.assert_called_once()
            mock_layer_instance.group_add.assert_called_once()

    @pytest.mark.asyncio
    async def test_listen_prices__handles_price_events(self):
        """Test listen_prices handles price events"""
        with patch("modules.prices.services.get_channel_layer") as mock_layer:
            mock_layer_instance = AsyncMock()
            mock_layer.return_value = mock_layer_instance

            event_data = {"AAPL": {"close": 150.0}}
            mock_layer_instance.receive.side_effect = [
                {"data": event_data},
                KeyboardInterrupt(),
            ]
            mock_layer_instance.new_channel.return_value = "test_channel"

            with contextlib.suppress(KeyboardInterrupt):
                await self.service.listen_prices()

            self.mock_handler.handle.assert_called_once_with(prices=event_data)

    @pytest.mark.asyncio
    async def test_listen_prices__cleans_up_on_exit(self):
        """Test listen_prices cleans up group membership on exit"""
        with patch("modules.prices.services.get_channel_layer") as mock_layer:
            mock_layer_instance = AsyncMock()
            mock_layer.return_value = mock_layer_instance

            mock_layer_instance.receive.side_effect = KeyboardInterrupt()
            mock_layer_instance.new_channel.return_value = "test_channel"

            with contextlib.suppress(KeyboardInterrupt):
                await self.service.listen_prices()

            mock_layer_instance.group_discard.assert_called_once()
