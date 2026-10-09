from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Приложение ---
    app_name: str = "PassVault API"
    app_version: str = "0.1.0"
    environment: str = "dev"
    debug: bool = True
    docs_enabled: bool = True
    api_prefix: str = "/api"

    # --- CORS ---
    # NoDecode: не парсить значение из .env как JSON, отдать сырую строку
    # в валидатор ниже (который сам разберёт "a,b,c").
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173", "http://localhost:3000"
    ]

    # --- Rate limiting ---
    rate_limit_default: str = "120/minute"
    rate_limit_write: str = "30/minute"
    rate_limit_auth: str = "5/minute"
    rate_limit_storage_uri: str = ""

    # --- Размер тела запроса ---
    max_request_body_bytes: int = 3 * 1024 * 1024

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
