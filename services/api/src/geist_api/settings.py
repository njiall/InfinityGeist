"""Application settings using pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API settings with GEIST_API_* prefix."""

    model_config = SettingsConfigDict(
        env_prefix="GEIST_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ChromaDB persistence path
    CHROMA_PATH: str = "data/chroma"


# Global settings instance
settings = Settings()
