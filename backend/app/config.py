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

    # Experimentation
    # Active experiment key for chat - set to empty string to auto-select from DB
    active_experiment_key: str = ""

    # Streaming limits
    max_concurrent_streams_per_user: int = 5  # Max simultaneous streams per user
    stream_timeout_seconds: int = 120  # Max duration for a single stream
    llm_response_timeout_seconds: int = 60  # Timeout for LLM provider response

    # Rust Token Counter Service
    token_counter_url: str = "http://localhost:3001"
    token_counter_enabled: bool = True
    token_counter_timeout: float = 0.5  # seconds - fail fast to avoid blocking

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
