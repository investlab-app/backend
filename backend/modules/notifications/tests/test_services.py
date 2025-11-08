from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from channels.db import database_sync_to_async

from modules.notifications.models import PushSubscription
from modules.notifications.services import (
    EmailPayload,
    EmailService,
    NotificationService,
    PushPayload,
    PushService,
    WebSocketPayload,
    WebSocketService,
)


@pytest.mark.django_db
class TestEmailService:
    """Tests for EmailService"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = EmailService()

    @patch("modules.notifications.services.send_mail")
    def test_sync_send_email__success__returns_true(self, mock_send_mail):
        """Test successful email sending"""
        result = self.service.sync_send_email(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body",
        )

        assert result is True
        mock_send_mail.assert_called_once()

    @patch("modules.notifications.services.send_mail")
    def test_sync_send_email__failure__returns_false(self, mock_send_mail):
        """Test email sending failure"""
        mock_send_mail.side_effect = Exception("SMTP Error")

        result = self.service.sync_send_email(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("modules.notifications.services.send_mail")
    async def test_send_email__async__returns_true(self, mock_send_mail):
        """Test async email sending"""
        result = await self.service.send_email(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body",
        )

        assert result is True


@pytest.mark.django_db
class TestPushService:
    """Tests for PushService"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = PushService()

    @patch("modules.notifications.services.webpush")
    def test_sync_send_push__success__returns_true(self, mock_webpush):
        """Test successful push notification"""
        subscription = MagicMock(spec=PushSubscription)
        subscription.endpoint = "https://example.com/push"
        subscription.p256dh = "test_p256dh"
        subscription.auth = "test_auth"

        result = self.service.sync_send_push(
            subscription=subscription,
            title="Test Title",
            body="Test Body",
        )

        assert result is True
        mock_webpush.assert_called_once()

    @patch("modules.notifications.services.webpush")
    def test_sync_send_push__webpush_exception__returns_false(self, mock_webpush):
        """Test push notification with WebPushException"""
        from pywebpush import WebPushException

        mock_webpush.side_effect = WebPushException("Invalid subscription")
        subscription = MagicMock(spec=PushSubscription)

        result = self.service.sync_send_push(
            subscription=subscription,
            title="Test Title",
            body="Test Body",
        )

        assert result is False

    @patch("modules.notifications.services.webpush")
    def test_sync_send_push__unexpected_error__returns_false(self, mock_webpush):
        """Test push notification with unexpected error"""
        mock_webpush.side_effect = Exception("Unexpected error")
        subscription = MagicMock(spec=PushSubscription)

        result = self.service.sync_send_push(
            subscription=subscription,
            title="Test Title",
            body="Test Body",
        )

        assert result is False

    @pytest.mark.asyncio
    @patch("modules.notifications.services.webpush")
    async def test_send_push__async__returns_true(self, mock_webpush):
        """Test async push notification sending"""
        subscription = MagicMock(spec=PushSubscription)
        subscription.endpoint = "https://example.com/push"
        subscription.p256dh = "test_p256dh"
        subscription.auth = "test_auth"

        result = await self.service.send_push(
            subscription=subscription,
            title="Test Title",
            body="Test Body",
        )

        assert result is True


@pytest.mark.django_db
class TestWebSocketService:
    """Tests for WebSocketService"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_channel_layer = AsyncMock()
        self.service = WebSocketService(channel_layer=self.mock_channel_layer)

    @pytest.mark.asyncio
    async def test_send_websocket_notification__success__returns_true(self):
        """Test successful WebSocket notification"""
        investor_id = "test-investor-123"
        message = {"type": "order_created", "order_id": "ord-123"}

        result = await self.service.send_websocket_notification(
            investor_id=investor_id,
            message=message,
        )

        assert result is True
        self.mock_channel_layer.group_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_websocket_notification__error__returns_false(self):
        """Test WebSocket notification with error"""
        self.mock_channel_layer.group_send.side_effect = Exception(
            "Channel layer error"
        )

        result = await self.service.send_websocket_notification(
            investor_id="test-investor-123",
            message={"type": "test"},
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_websocket_notification__formats_group_name(self):
        """Test WebSocket notification formats group name correctly"""
        investor_id = "test-investor-456"

        await self.service.send_websocket_notification(
            investor_id=investor_id,
            message={"type": "test"},
        )

        call_args = self.mock_channel_layer.group_send.call_args
        group_name = call_args[0][0]
        assert group_name == f"investor_{investor_id}"


@pytest.mark.django_db
class TestNotificationService:
    """Tests for NotificationService"""

    @pytest.fixture(autouse=True)
    def setup(self, investor_factory):
        self.investor = investor_factory()
        self.mock_email_service = AsyncMock()
        self.mock_push_service = AsyncMock()
        self.mock_websocket_service = AsyncMock()
        self.mock_clerk_user_service = MagicMock()

        self.service = NotificationService(
            email_service=self.mock_email_service,
            push_service=self.mock_push_service,
            websocket_service=self.mock_websocket_service,
            clerk_user_service=self.mock_clerk_user_service,
        )

    @pytest.mark.asyncio
    async def test_send_email_notification__calls_email_service(self):
        """Test email notification calls email service"""
        self.mock_clerk_user_service.get_user_email_addresses.return_value = [
            "test@example.com"
        ]

        payload = EmailPayload(
            subject="Test Email",
            body="This is a test email",
        )

        await self.service.send_email_notification(
            investor=self.investor,
            email_payload=payload,
        )

        self.mock_email_service.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_notification__passes_correct_arguments(self):
        """Test email notification passes correct arguments"""
        self.mock_clerk_user_service.get_user_email_addresses.return_value = [
            "test@example.com"
        ]

        payload = EmailPayload(
            subject="Test Subject",
            body="Test Body",
        )

        await self.service.send_email_notification(
            investor=self.investor,
            email_payload=payload,
        )

        call_args = self.mock_email_service.send_email.call_args
        assert call_args.kwargs["subject"] == "Test Subject"
        assert call_args.kwargs["body"] == "Test Body"
        assert "test@example.com" in call_args.kwargs["to"]

    @pytest.mark.asyncio
    async def test_send_push_notifications__no_subscriptions(self):
        """Test push notification with no subscriptions"""
        payload = PushPayload(title="Test", body="Test Body")

        await self.service.send_push_notifications(
            investor=self.investor,
            push_payload=payload,
        )

        self.mock_push_service.send_push.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_push_notifications__with_subscriptions(self, investor_factory):
        """Test push notification with subscriptions"""

        def create_investor_and_subscription():
            investor = investor_factory()
            PushSubscription.objects.create(
                investor=investor,
                endpoint="https://example.com/push",
                p256dh="test_p256dh",
                auth="test_auth",
            )
            return investor

        investor = await database_sync_to_async(create_investor_and_subscription)()

        payload = PushPayload(title="Test Title", body="Test Body")

        await self.service.send_push_notifications(
            investor=investor,
            push_payload=payload,
        )

        self.mock_push_service.send_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_websocket_notifications__calls_websocket_service(self):
        """Test WebSocket notification calls service"""
        payload = WebSocketPayload(message={"type": "order_created"})

        await self.service.send_websocket_notifications(
            investor=self.investor,
            websocket_payload=payload,
        )

        self.mock_websocket_service.send_websocket_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_websocket_notifications__passes_investor_id(self):
        """Test WebSocket notification passes correct investor ID"""
        payload = WebSocketPayload(message={"type": "test"})

        await self.service.send_websocket_notifications(
            investor=self.investor,
            websocket_payload=payload,
        )

        call_args = self.mock_websocket_service.send_websocket_notification.call_args
        assert call_args.kwargs["investor_id"] == str(self.investor.id)
