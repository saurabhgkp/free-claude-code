"""Messaging platform factory."""

from loguru import logger

from .base import MessagingPlatform


def create_messaging_platform(**kwargs) -> MessagingPlatform | None:
    bot_token = kwargs.get("bot_token")
    if not bot_token:
        logger.info("No Telegram bot token configured, skipping platform setup")
        return None

    from .telegram import TelegramPlatform

    return TelegramPlatform(
        bot_token=bot_token,
        allowed_user_id=kwargs.get("allowed_user_id"),
    )
