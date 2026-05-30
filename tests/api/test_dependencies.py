from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.dependencies import (
    cleanup_provider,
    get_provider,
    get_provider_for_type,
    get_settings,
)
from config.nim import NimSettings
from providers.nvidia_nim import NvidiaNimProvider


def _make_mock_settings(**overrides):
    mock = MagicMock()
    mock.model = "nvidia_nim/meta/llama3"
    mock.provider_type = "nvidia_nim"
    mock.nvidia_nim_api_key = "test_key"
    mock.provider_rate_limit = 40
    mock.provider_rate_window = 60
    mock.provider_max_concurrency = 5
    mock.nim = NimSettings()
    mock.http_read_timeout = 300.0
    mock.http_write_timeout = 10.0
    mock.http_connect_timeout = 2.0
    for key, value in overrides.items():
        setattr(mock, key, value)
    return mock


@pytest.fixture(autouse=True)
def reset_provider():
    import api.dependencies

    saved = api.dependencies._providers
    api.dependencies._providers = {}
    yield
    api.dependencies._providers = saved


@pytest.mark.asyncio
async def test_get_provider_singleton():
    with patch("api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = _make_mock_settings()

        p1 = get_provider()
        p2 = get_provider()

        assert isinstance(p1, NvidiaNimProvider)
        assert p1 is p2


@pytest.mark.asyncio
async def test_get_settings():
    settings = get_settings()
    assert settings is not None
    with patch("api.dependencies._get_settings") as mock_get:
        get_settings()
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_provider():
    with patch("api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = _make_mock_settings()

        provider = get_provider()
        assert isinstance(provider, NvidiaNimProvider)
        provider._client = AsyncMock()

        await cleanup_provider()

        provider._client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_provider_no_client():
    with patch("api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = _make_mock_settings()

        provider = get_provider()
        if hasattr(provider, "_client"):
            del provider._client

        await cleanup_provider()


@pytest.mark.asyncio
async def test_get_provider_passes_http_timeouts_from_settings():
    with (
        patch("api.dependencies.get_settings") as mock_settings,
        patch("providers.openai_compat.AsyncOpenAI") as mock_openai,
    ):
        mock_settings.return_value = _make_mock_settings(
            http_read_timeout=600.0,
            http_write_timeout=20.0,
            http_connect_timeout=5.0,
        )
        provider = get_provider()
        assert isinstance(provider, NvidiaNimProvider)
        call_kwargs = mock_openai.call_args[1]
        timeout = call_kwargs["timeout"]
        assert timeout.read == 600.0
        assert timeout.write == 20.0
        assert timeout.connect == 5.0


@pytest.mark.asyncio
async def test_get_provider_nvidia_nim_missing_api_key():
    with patch("api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = _make_mock_settings(nvidia_nim_api_key="")

        with pytest.raises(HTTPException) as exc_info:
            get_provider()

        assert exc_info.value.status_code == 503
        assert "NVIDIA_NIM_API_KEY" in exc_info.value.detail
        assert "build.nvidia.com" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_provider_nvidia_nim_whitespace_only_api_key():
    with patch("api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = _make_mock_settings(nvidia_nim_api_key="   ")

        with pytest.raises(HTTPException) as exc_info:
            get_provider()

        assert exc_info.value.status_code == 503
        assert "NVIDIA_NIM_API_KEY" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_provider_for_type_caches():
    with patch("api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = _make_mock_settings()

        p1 = get_provider_for_type("nvidia_nim")
        p2 = get_provider_for_type("nvidia_nim")

        assert p1 is p2
        assert isinstance(p1, NvidiaNimProvider)


@pytest.mark.asyncio
async def test_cleanup_provider_aclose_raises():
    with patch("api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = _make_mock_settings()

        provider = get_provider()
        assert isinstance(provider, NvidiaNimProvider)
        provider._client = AsyncMock()
        provider._client.aclose = AsyncMock(side_effect=RuntimeError("cleanup failed"))

        with pytest.raises(RuntimeError, match="cleanup failed"):
            await cleanup_provider()
