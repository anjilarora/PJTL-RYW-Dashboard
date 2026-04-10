from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RYW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", description="development | staging | production")
    cors_origins: str = Field(
        default="",
        description="Comma-separated allowed origins; empty uses localhost defaults",
    )
    auth_mode: Literal["header", "jwt"] = "header"
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_role_claim: str = "role"
    internal_api_secret: str | None = Field(
        default=None,
        description="If set, require matching X-Internal-Secret on /api/v1/* (except /health, /ready)",
    )
    enable_operations_demo: bool = True
    rate_limit_evaluate: str = "60/minute"
    rate_limit_predict: str = "120/minute"
    log_level: str = Field(
        default="INFO",
        description="Python logging level: DEBUG, INFO, WARNING, ERROR",
    )
    expose_internal_errors: bool = Field(
        default=False,
        description="If True, 500 responses include exception text (never in public production).",
    )

    @field_validator("internal_api_secret", mode="before")
    @classmethod
    def _empty_secret_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if not raw:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://frontend:3000",
            ]
        return [x.strip() for x in raw.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
