"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "PromptLab"
    debug: bool = False

    # Database
    database_url: str

    # Redis
    redis_url: str

    # OpenAI
    openai_api_key: str

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # seconds (1 hour)

    # API Keys (for initial setup)
    admin_api_key: str = "admin-key-change-in-production"

    # CORS
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
