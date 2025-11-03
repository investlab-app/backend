"""
Notification helpers for sending messages to investors via WebSocket.
"""

import json
import logging
from typing import Any

from channels.layers import get_channel_layer
from django.apps import apps

logger = logging.getLogger(__name__)


async def send_notification_to_investor(
    investor_id: str,
    title: str,
    body: str,
    notification_type: str = "info",
) -> bool:
    """
    Send a notification to a specific investor via WebSocket.

    Args:
        investor_id: The investor's UUID as string
        title: Notification title
        body: Notification body/message
        notification_type: Type of notification (info, warning, error, success)

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        channel_layer = get_channel_layer()

        notification_data = {
            "type": "notification_receive",
            "notification": {
                "type": notification_type,
                "title": title,
                "body": body,
            },
        }

        # Send to investor's notification group
        await channel_layer.group_send(
            f"investor_notifications_{investor_id}",
            notification_data,
        )

        logger.info(f"Notification sent to investor {investor_id}: {title}")
        return True

    except Exception as e:
        logger.exception(f"Failed to send notification to investor {investor_id}: {e}")
        return False


async def send_notification_to_multiple_investors(
    investor_ids: list[str],
    title: str,
    body: str,
    notification_type: str = "info",
) -> dict[str, bool]:
    """
    Send the same notification to multiple investors.

    Args:
        investor_ids: List of investor UUIDs as strings
        title: Notification title
        body: Notification body/message
        notification_type: Type of notification

    Returns:
        Dictionary mapping investor_id to success status
    """
    results = {}

    for investor_id in investor_ids:
        results[investor_id] = await send_notification_to_investor(
            investor_id=investor_id,
            title=title,
            body=body,
            notification_type=notification_type,
        )

    return results


def create_price_alert_notification(
    symbol: str,
    current_price: float,
    alert_type: str,
    threshold: float,
) -> tuple[str, str]:
    """
    Create a price alert notification.

    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        current_price: Current price
        alert_type: 'above' or 'below'
        threshold: Threshold price

    Returns:
        Tuple of (title, body)
    """
    title = f"Price Alert: {symbol}"
    direction = "above" if alert_type == "above" else "below"
    body = (
        f"{symbol} is now trading {direction} ${threshold:.2f} at ${current_price:.2f}"
    )
    return title, body


def create_order_notification(
    symbol: str,
    order_type: str,
    quantity: float,
    price: float,
    status: str,
) -> tuple[str, str]:
    """
    Create an order notification.

    Args:
        symbol: Stock symbol
        order_type: 'buy' or 'sell'
        quantity: Order quantity
        price: Order price
        status: 'executed', 'cancelled', 'pending', etc.

    Returns:
        Tuple of (title, body)
    """
    action = "Buy" if order_type == "buy" else "Sell"
    title = f"Order {status.title()}: {action} {symbol}"
    body = f"{action} order for {quantity} shares of {symbol} at ${price:.2f} has been {status}."
    return title, body


def create_portfolio_update_notification(
    portfolio_value: float,
    daily_change: float,
    daily_change_percent: float,
) -> tuple[str, str]:
    """
    Create a portfolio update notification.

    Args:
        portfolio_value: Total portfolio value
        daily_change: Daily value change in dollars
        daily_change_percent: Daily change in percentage

    Returns:
        Tuple of (title, body)
    """
    direction = "📈" if daily_change >= 0 else "📉"
    title = f"Portfolio Update {direction}"
    sign = "+" if daily_change >= 0 else ""
    body = (
        f"Your portfolio is now worth ${portfolio_value:,.2f}. "
        f"Daily change: {sign}${daily_change:.2f} ({sign}{daily_change_percent:.2f}%)"
    )
    return title, body


def create_milestone_notification(
    milestone_type: str,
    milestone_value: Any,
) -> tuple[str, str]:
    """
    Create a milestone achievement notification.

    Args:
        milestone_type: Type of milestone (e.g., 'portfolio_value', 'trades_count', 'first_profit')
        milestone_value: Value associated with the milestone

    Returns:
        Tuple of (title, body)
    """
    milestones = {
        "portfolio_value": (
            f"🎉 Portfolio Milestone",
            f"Your portfolio has reached ${milestone_value:,.2f}!",
        ),
        "trades_count": (
            f"📊 Trading Milestone",
            f"You have completed {milestone_value} trades!",
        ),
        "first_profit": (
            f"💰 First Profit!",
            f"Congratulations on your first profitable trade!",
        ),
        "win_streak": (
            f"🔥 Win Streak",
            f"You have {milestone_value} consecutive winning trades!",
        ),
    }

    return milestones.get(
        milestone_type,
        ("Milestone Reached", f"You've reached a new milestone: {milestone_value}"),
    )


def create_system_notification(
    message: str,
    notification_type: str = "info",
) -> tuple[str, str]:
    """
    Create a system notification.

    Args:
        message: The message content
        notification_type: Type of notification

    Returns:
        Tuple of (title, body)
    """
    type_titles = {
        "info": "ℹ️ Information",
        "warning": "⚠️ Warning",
        "error": "❌ Error",
        "success": "✅ Success",
    }

    title = type_titles.get(notification_type, "System Notification")
    return title, message
