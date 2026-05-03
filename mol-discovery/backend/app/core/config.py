from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DEBUG: bool = False

    # Postgres (asyncpg driver)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:changeme123@localhost:5432/moldiscovery"
    # TimescaleDB shares the same Postgres instance by default
    TIMESCALE_URL: str = "postgresql+asyncpg://postgres:changeme123@localhost:5432/moldiscovery"

    QDRANT_URL: str = "http://localhost:6333"
    NEO4J_URI: str = "bolt://localhost:7687"
    REDIS_URL: str = "redis://localhost:6379"

    SECRET_KEY: str = "change-me-in-production"

    # External API keys – all optional; ingestor falls back to synthetic data
    OPENAI_API_KEY: Optional[str] = None
    BRENDA_API_KEY: Optional[str] = None
    MP_API_KEY: Optional[str] = None          # Materials Project
    OPENCATALYST_MODEL_PATH: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

