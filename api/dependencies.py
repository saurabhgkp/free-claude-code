"""Dependency injection for FastAPI."""

from fastapi import HTTPException
from loguru import logger

from config.settings import Settings
from config.settings import get_settings as _get_settings
from providers.base import BaseProvider, ProviderConfig
from providers.common import get_user_facing_error_message
from providers.exceptions import AuthenticationError
from providers.nvidia_nim import NVIDIA_NIM_BASE_URL, NvidiaNimProvider

_providers: dict[str, BaseProvider] = {}


def get_settings() -> Settings:
    return _get_settings()


def _create_provider(settings: Settings) -> BaseProvider:
    if not settings.nvidia_nim_api_key.strip():
        raise AuthenticationError(
            "NVIDIA_NIM_API_KEY is not set. "
            "Get a key at https://build.nvidia.com/settings/api-keys"
        )
    config = ProviderConfig(
        api_key=settings.nvidia_nim_api_key,
        base_url=NVIDIA_NIM_BASE_URL,
        rate_limit=settings.provider_rate_limit,
        rate_window=settings.provider_rate_window,
        max_concurrency=settings.provider_max_concurrency,
        http_read_timeout=settings.http_read_timeout,
        http_write_timeout=settings.http_write_timeout,
        http_connect_timeout=settings.http_connect_timeout,
    )
    return NvidiaNimProvider(config, nim_settings=settings.nim)


def get_provider_for_type(provider_type: str) -> BaseProvider:
    if provider_type not in _providers:
        try:
            _providers[provider_type] = _create_provider(get_settings())
        except AuthenticationError as e:
            raise HTTPException(
                status_code=503, detail=get_user_facing_error_message(e)
            ) from e
        logger.info("Provider initialized: {}", provider_type)
    return _providers[provider_type]


def get_provider() -> BaseProvider:
    return get_provider_for_type(get_settings().provider_type)


async def cleanup_provider():
    global _providers
    for provider in _providers.values():
        await provider.cleanup()
    _providers = {}
    logger.debug("Provider cleanup completed")
