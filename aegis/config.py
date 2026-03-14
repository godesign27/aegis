"""Aegis configuration — loaded from environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required
    anthropic_api_key: str = ""

    # Optional
    github_token: str = ""
    aegis_env: str = "development"
    aegis_log_level: str = "INFO"
    aegis_max_concurrent_audits: int = 5
    aegis_audit_timeout_seconds: int = 120

    # Model selection
    claude_model: str = "claude-sonnet-4-5"

    @property
    def is_production(self) -> bool:
        return self.aegis_env == "production"


settings = Settings()
