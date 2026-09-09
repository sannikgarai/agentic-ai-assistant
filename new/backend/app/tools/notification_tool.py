"""
Notification tool.

Provides a common interface for sending notifications.
Email, SMS, push notifications, or other providers can
be connected later.
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable


NotificationProvider = Callable[
    [str, str, str | None],
    Awaitable[Any],
]


class NotificationTool:
    """Agent notification tool."""

    name = "notification"

    description = (
        "Send notifications about application status, "
        "verification results, or workflow events."
    )

    def __init__(
        self,
        provider: NotificationProvider | None = None,
    ):
        self.provider = provider

    async def execute(
        self,
        recipient: str,
        message: str,
        channel: str = "email",
        subject: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a notification."""

        if not isinstance(recipient, str) or not recipient.strip():
            return {
                "success": False,
                "message": "Recipient is required.",
            }

        if not isinstance(message, str) or not message.strip():
            return {
                "success": False,
                "message": "Notification message is required.",
            }

        if not isinstance(channel, str) or not channel.strip():
            return {
                "success": False,
                "message": "Notification channel is required.",
            }

        recipient = recipient.strip()
        message = message.strip()
        channel = channel.strip().lower()

        if isinstance(subject, str):
            subject = subject.strip() or None

        supported_channels = {
            "email",
            "sms",
            "push",
        }

        if channel not in supported_channels:
            return {
                "success": False,
                "message": (
                    f"Unsupported notification channel: "
                    f"{channel}"
                ),
                "supported_channels": sorted(
                    supported_channels
                ),
            }

        if self.provider is None:
            return {
                "success": True,
                "status": "not_connected",
                "recipient": recipient,
                "channel": channel,
                "subject": subject,
                "message": message,
                "notification_sent": False,
                "info": (
                    "Notification provider is not connected yet."
                ),
            }

        try:
            result = self.provider(
                recipient,
                message,
                subject,
            )

            if hasattr(result, "__await__"):
                result = await result

            return {
                "success": True,
                "status": "sent",
                "recipient": recipient,
                "channel": channel,
                "result": result,
            }

        except Exception as exc:
            return {
                "success": False,
                "status": "failed",
                "recipient": recipient,
                "channel": channel,
                "error": str(exc),
                "message": (
                    "Notification could not be sent."
                ),
            }