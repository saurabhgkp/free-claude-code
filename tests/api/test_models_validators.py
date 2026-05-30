from unittest.mock import patch

import pytest

from api.models.anthropic import Message, MessagesRequest, TokenCountRequest
from config.settings import Settings


@pytest.fixture
def mock_settings():
    settings = Settings()
    settings.model = "nvidia_nim/target-model-from-settings"
    return settings


def test_messages_request_map_model_claude_to_default(mock_settings):
    with patch("api.models.anthropic.get_settings", return_value=mock_settings):
        request = MessagesRequest(
            model="claude-3-opus",
            max_tokens=100,
            messages=[Message(role="user", content="hello")],
        )

        assert request.model == "target-model-from-settings"
        assert request.original_model == "claude-3-opus"


def test_messages_request_map_model_with_provider_prefix(mock_settings):
    with patch("api.models.anthropic.get_settings", return_value=mock_settings):
        request = MessagesRequest(
            model="anthropic/claude-3-haiku",
            max_tokens=100,
            messages=[Message(role="user", content="hello")],
        )

        assert request.model == "target-model-from-settings"


def test_token_count_request_model_validation(mock_settings):
    with patch("api.models.anthropic.get_settings", return_value=mock_settings):
        request = TokenCountRequest(
            model="claude-3-sonnet", messages=[Message(role="user", content="hello")]
        )

        assert request.model == "target-model-from-settings"


def test_messages_request_model_mapping_logs(mock_settings):
    with (
        patch("api.models.anthropic.get_settings", return_value=mock_settings),
        patch("api.models.anthropic.logger.debug") as mock_log,
    ):
        MessagesRequest(
            model="claude-2.1",
            max_tokens=100,
            messages=[Message(role="user", content="hello")],
        )

        mock_log.assert_called()
        args = mock_log.call_args[0][0]
        assert "MODEL MAPPING" in args
        assert "claude-2.1" in args
        assert "target-model-from-settings" in args


def test_messages_request_resolved_provider_model_default(mock_settings):
    with patch("api.models.anthropic.get_settings", return_value=mock_settings):
        request = MessagesRequest(
            model="claude-3-opus",
            max_tokens=100,
            messages=[Message(role="user", content="hello")],
        )
        assert (
            request.resolved_provider_model == "nvidia_nim/target-model-from-settings"
        )


def test_messages_request_model_fallback():
    """All Claude model names fall back to MODEL."""
    settings = Settings()
    settings.model = "nvidia_nim/fallback-model"

    with patch("api.models.anthropic.get_settings", return_value=settings):
        for model_name in [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-haiku-20240307",
            "claude-2.1",
        ]:
            request = MessagesRequest(
                model=model_name,
                max_tokens=100,
                messages=[Message(role="user", content="hello")],
            )
            assert request.model == "fallback-model"
            assert request.resolved_provider_model == "nvidia_nim/fallback-model"


def test_token_count_request_model_aware():
    settings = Settings()
    settings.model = "nvidia_nim/fallback-model"

    with patch("api.models.anthropic.get_settings", return_value=settings):
        request = TokenCountRequest(
            model="claude-3-haiku-20240307",
            messages=[Message(role="user", content="hello")],
        )
        assert request.model == "fallback-model"
