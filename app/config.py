"""Configuration helpers for the Research service.

This module deliberately keeps environment parsing logic in one place so
engineers inheriting the codebase understand where runtime behaviour is
controlled.  Detailed comments are included per the project's knowledge
transfer standards.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import EnvSettingsSource


class LenientEnvSettingsSource(EnvSettingsSource):
    """Custom env loader that falls back to raw strings for complex values."""

    def decode_complex_value(self, field_name: str, field: FieldInfo, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        return super().decode_complex_value(field_name, field, value)


class ResearchSettings(BaseSettings):
    """Strongly-typed model exposing runtime configuration.

    Fields are annotated with clear defaults to make handoffs effortless when a
    new engineer extends the service.  Validators contain verbose inline
    comments so future maintainers know why each branch exists.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        """Inject the lenient env source ahead of the default implementation."""

        return (
            init_settings,
            LenientEnvSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    app_name: str = Field(default="plasma-engine-research", description="Human readable service name")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Origins allowed by CORS when the API is accessed from browsers",
    )
    openai_api_key: str | None = Field(
        default=None,
        description="Optional key used by downstream research pipelines when calling OpenAI APIs",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _coerce_cors_origins(cls, raw_value: Any) -> list[str]:
        """Allow environment overrides expressed as JSON arrays or comma strings."""

        # Short-circuit when the value is already a sequence of strings.
        if isinstance(raw_value, (list, tuple, set)):
            return [str(origin).strip() for origin in raw_value if str(origin).strip()]

        if isinstance(raw_value, str):
            candidate = raw_value.strip()
            if not candidate:
                return []

            # Prefer JSON input so operators can set CORS_ORIGINS='["a","b"]'.
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                parsed = None

            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            if isinstance(parsed, str):
                return [parsed.strip()] if parsed.strip() else []

            # Fall back to comma-separated values for ergonomic env vars.
            return [origin.strip() for origin in candidate.split(",") if origin.strip()]

        # Defer to BaseSettings for anything else (e.g. None).
        return raw_value


@lru_cache
def get_settings() -> ResearchSettings:
    """Return a cached settings instance to avoid reparsing environment variables."""

    return ResearchSettings()

