"""Configuration settings for the ML API."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    app_name: str = "ML Model Serving API"
    version: str = "0.1.0"
    debug: bool = False

    # Model configuration
    model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"
    model_cache_dir: Optional[str] = "./model_cache"

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS settings
    allow_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
