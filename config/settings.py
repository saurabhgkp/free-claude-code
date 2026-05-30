"""Centralized configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .nim import NimSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ==================== NVIDIA NIM ====================
    nvidia_nim_api_key: str = ""

    # ==================== Model ====================
    model: str = "nvidia_nim/stepfun-ai/step-3.5-flash"

    # ==================== Provider Rate Limiting ====================
    provider_rate_limit: int = Field(default=40, validation_alias="PROVIDER_RATE_LIMIT")
    provider_rate_window: int = Field(default=60, validation_alias="PROVIDER_RATE_WINDOW")
    provider_max_concurrency: int = Field(
        default=5, validation_alias="PROVIDER_MAX_CONCURRENCY"
    )

    # ==================== HTTP Client Timeouts ====================
    http_read_timeout: float = Field(default=300.0, validation_alias="HTTP_READ_TIMEOUT")
    http_write_timeout: float = Field(default=10.0, validation_alias="HTTP_WRITE_TIMEOUT")
    http_connect_timeout: float = Field(
        default=2.0, validation_alias="HTTP_CONNECT_TIMEOUT"
    )

    # ==================== Optimizations ====================
    fast_prefix_detection: bool = True
    enable_network_probe_mock: bool = True
    enable_title_generation_skip: bool = True
    enable_suggestion_mode_skip: bool = True
    enable_filepath_extraction_mock: bool = True

    # ==================== NIM Settings ====================
    nim: NimSettings = Field(default_factory=NimSettings)

    # ==================== Context Window ====================
    model_context_window: str = Field(
        default="", validation_alias="MODEL_CONTEXT_WINDOW"
    )
    context_window_safety_margin: int = Field(
        default=100, validation_alias="CONTEXT_WINDOW_SAFETY_MARGIN"
    )

    # ==================== Telegram Bot ====================
    telegram_bot_token: str | None = None
    allowed_telegram_user_id: str | None = None

    # ==================== Agent Config ====================
    claude_workspace: str = "./agent_workspace"
    allowed_dir: str = ""

    # ==================== Server ====================
    host: str = "0.0.0.0"
    port: int = 8082
    log_file: str = "server.log"

    @field_validator("telegram_bot_token", "allowed_telegram_user_id", mode="before")
    @classmethod
    def parse_optional_str(cls, v):
        return None if v == "" else v

    @field_validator("model")
    @classmethod
    def validate_model_format(cls, v: str) -> str:
        if "/" not in v or not v.startswith("nvidia_nim/"):
            raise ValueError(
                "MODEL must be in format 'nvidia_nim/model/name'. "
                "Only NVIDIA NIM is supported."
            )
        return v

    def resolve_model(self, claude_model_name: str) -> str:
        """Map any Claude model name to the configured NVIDIA NIM model."""
        return self.model

    @property
    def provider_type(self) -> str:
        return "nvidia_nim"

    @property
    def model_name(self) -> str:
        return self.model.split("/", 1)[1]

    @staticmethod
    def parse_provider_type(model_string: str) -> str:
        return model_string.split("/", 1)[0]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
