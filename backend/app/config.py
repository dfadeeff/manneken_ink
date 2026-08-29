import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./manneken.db"
    cors_origins: str = "http://localhost:3000"

    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    clerk_jwks_url: str = ""
    dev_auth_bypass: bool = False

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""

    router_policy: Literal["balanced", "cost", "speed"] = "balanced"
    router_tier_overrides: str = ""

    # Guardrail limits. Deliberately conservative: these users are 7-10 years old.
    max_message_chars: int = 500
    messages_per_minute: int = 20
    messages_per_day: int = 400

    @model_validator(mode="after")
    def _guard_dev_bypass(self):
        if self.dev_auth_bypass and self.environment != "development":
            raise ValueError("DEV_AUTH_BYPASS is only allowed when ENVIRONMENT=development")
        return self

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def tier_overrides(self) -> dict[str, str]:
        if not self.router_tier_overrides.strip():
            return {}
        return json.loads(self.router_tier_overrides)


@lru_cache
def get_settings() -> Settings:
    return Settings()
