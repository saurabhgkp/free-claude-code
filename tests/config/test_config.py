"""Tests for config/settings.py and config/nim.py"""

import pytest
from pydantic import ValidationError

from config.nim import NimSettings


class TestSettings:
    def test_settings_loads(self):
        from config.settings import Settings

        settings = Settings()
        assert settings is not None

    def test_default_values(self):
        from config.settings import Settings

        settings = Settings()
        assert isinstance(settings.provider_rate_limit, int)
        assert isinstance(settings.provider_rate_window, int)
        assert isinstance(settings.nim.temperature, float)
        assert isinstance(settings.fast_prefix_detection, bool)

    def test_get_settings_cached(self):
        from config.settings import get_settings

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_model_setting(self):
        from config.settings import Settings

        settings = Settings()
        assert isinstance(settings.model, str)
        assert settings.model.startswith("nvidia_nim/")

    def test_base_url_constant(self):
        from providers.nvidia_nim import NVIDIA_NIM_BASE_URL

        assert NVIDIA_NIM_BASE_URL == "https://integrate.api.nvidia.com/v1"

    def test_provider_rate_limit_from_env(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("PROVIDER_RATE_LIMIT", "20")
        settings = Settings()
        assert settings.provider_rate_limit == 20

    def test_provider_rate_window_from_env(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("PROVIDER_RATE_WINDOW", "30")
        settings = Settings()
        assert settings.provider_rate_window == 30

    def test_http_read_timeout_from_env(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("HTTP_READ_TIMEOUT", "600")
        settings = Settings()
        assert settings.http_read_timeout == 600.0

    def test_http_write_timeout_from_env(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("HTTP_WRITE_TIMEOUT", "20")
        settings = Settings()
        assert settings.http_write_timeout == 20.0

    def test_http_connect_timeout_from_env(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("HTTP_CONNECT_TIMEOUT", "5")
        settings = Settings()
        assert settings.http_connect_timeout == 5.0

    def test_model_invalid_provider_raises(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("MODEL", "open_router/some/model")
        with pytest.raises(ValidationError):
            Settings()

    def test_model_no_slash_raises(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("MODEL", "noprefix")
        with pytest.raises(ValidationError):
            Settings()

    def test_resolve_model_always_returns_model(self):
        from config.settings import Settings

        s = Settings()
        model = s.model
        assert s.resolve_model("claude-opus-4-20250514") == model
        assert s.resolve_model("claude-sonnet-4-20250514") == model
        assert s.resolve_model("claude-haiku-4") == model

    def test_provider_type_is_nvidia_nim(self):
        from config.settings import Settings

        s = Settings()
        assert s.provider_type == "nvidia_nim"

    def test_parse_provider_type(self):
        from config.settings import Settings

        assert Settings.parse_provider_type("nvidia_nim/meta/llama") == "nvidia_nim"

    def test_parse_model_name(self):
        from config.settings import Settings

        assert Settings.parse_model_name("nvidia_nim/meta/llama") == "meta/llama"


class TestSettingsOptionalStr:
    def test_empty_telegram_token_to_none(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
        s = Settings()
        assert s.telegram_bot_token is None

    def test_valid_telegram_token_preserved(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc123")
        s = Settings()
        assert s.telegram_bot_token == "abc123"

    def test_empty_allowed_user_id_to_none(self, monkeypatch):
        from config.settings import Settings

        monkeypatch.setenv("ALLOWED_TELEGRAM_USER_ID", "")
        s = Settings()
        assert s.allowed_telegram_user_id is None


class TestNimSettingsValidBounds:
    @pytest.mark.parametrize("top_k", [-1, 0, 1, 100])
    def test_top_k_valid(self, top_k):
        s = NimSettings(top_k=top_k)
        assert s.top_k == top_k

    @pytest.mark.parametrize("temp", [0.0, 0.5, 1.0, 2.0])
    def test_temperature_valid(self, temp):
        s = NimSettings(temperature=temp)
        assert s.temperature == temp

    @pytest.mark.parametrize("top_p", [0.0, 0.5, 1.0])
    def test_top_p_valid(self, top_p):
        s = NimSettings(top_p=top_p)
        assert s.top_p == top_p

    @pytest.mark.parametrize("effort", ["low", "medium", "high"])
    def test_reasoning_effort_valid(self, effort):
        s = NimSettings(reasoning_effort=effort)
        assert s.reasoning_effort == effort

    def test_max_tokens_valid(self):
        s = NimSettings(max_tokens=1)
        assert s.max_tokens == 1

    def test_min_tokens_valid(self):
        s = NimSettings(min_tokens=0)
        assert s.min_tokens == 0

    @pytest.mark.parametrize("penalty", [-2.0, 0.0, 2.0])
    def test_presence_penalty_valid(self, penalty):
        s = NimSettings(presence_penalty=penalty)
        assert s.presence_penalty == penalty

    @pytest.mark.parametrize("penalty", [-2.0, 0.0, 2.0])
    def test_frequency_penalty_valid(self, penalty):
        s = NimSettings(frequency_penalty=penalty)
        assert s.frequency_penalty == penalty

    @pytest.mark.parametrize("min_p", [0.0, 0.5, 1.0])
    def test_min_p_valid(self, min_p):
        s = NimSettings(min_p=min_p)
        assert s.min_p == min_p


class TestNimSettingsInvalidBounds:
    @pytest.mark.parametrize("top_k", [-2, -100])
    def test_top_k_below_lower_bound(self, top_k):
        with pytest.raises((ValidationError, ValueError)):
            NimSettings(top_k=top_k)

    def test_temperature_negative(self):
        with pytest.raises(ValidationError):
            NimSettings(temperature=-0.1)

    @pytest.mark.parametrize("top_p", [-0.1, 1.1])
    def test_top_p_out_of_range(self, top_p):
        with pytest.raises(ValidationError):
            NimSettings(top_p=top_p)

    @pytest.mark.parametrize("penalty", [-2.1, 2.1])
    def test_presence_penalty_out_of_range(self, penalty):
        with pytest.raises(ValidationError):
            NimSettings(presence_penalty=penalty)

    @pytest.mark.parametrize("penalty", [-2.1, 2.1])
    def test_frequency_penalty_out_of_range(self, penalty):
        with pytest.raises(ValidationError):
            NimSettings(frequency_penalty=penalty)

    @pytest.mark.parametrize("min_p", [-0.1, 1.1])
    def test_min_p_out_of_range(self, min_p):
        with pytest.raises(ValidationError):
            NimSettings(min_p=min_p)

    @pytest.mark.parametrize("max_tokens", [0, -1])
    def test_max_tokens_too_low(self, max_tokens):
        with pytest.raises(ValidationError):
            NimSettings(max_tokens=max_tokens)

    def test_min_tokens_negative(self):
        with pytest.raises(ValidationError):
            NimSettings(min_tokens=-1)

    def test_reasoning_effort_invalid(self):
        from typing import Any, cast

        with pytest.raises(ValidationError):
            NimSettings(reasoning_effort=cast(Any, "invalid"))


class TestNimSettingsValidators:
    @pytest.mark.parametrize(
        "seed_val,expected",
        [("", None), (None, None), ("42", 42), (42, 42)],
        ids=["empty_str", "none", "str_42", "int_42"],
    )
    def test_parse_optional_int(self, seed_val, expected):
        s = NimSettings(seed=seed_val)
        assert s.seed == expected

    @pytest.mark.parametrize(
        "stop_val,expected",
        [("", None), ("STOP", "STOP"), (None, None)],
        ids=["empty_str", "valid", "none"],
    )
    def test_parse_optional_str_stop(self, stop_val, expected):
        s = NimSettings(stop=stop_val)
        assert s.stop == expected

    def test_extra_forbid_rejects_unknown_field(self):
        from typing import Any, cast

        with pytest.raises(ValidationError):
            NimSettings(**cast(Any, {"unknown_field": "value"}))
