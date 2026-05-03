from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    DEBUG: bool = True

    # Sync Postgres (psycopg2 driver) — used by all services
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/moldiscovery"

    # Optional services — not required for demo
    QDRANT_URL: str = "http://localhost:6333"
    NEO4J_URI: str = "bolt://localhost:7687"
    REDIS_URL: str = "redis://localhost:6379"

    API_SECRET_KEY: str = "moldiscovery-secret-key-2026"
    SECRET_KEY: str = "moldiscovery-secret-key-2026"
    MODEL_CACHE_PATH: str = "./models"

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]

    # External API keys — all optional; services fall back to synthetic data
    OPENAI_API_KEY: Optional[str] = None
    BRENDA_API_KEY: Optional[str] = None
    BRENDA_EMAIL: Optional[str] = None
    BRENDA_PASSWORD: Optional[str] = None
    MP_API_KEY: Optional[str] = None
    OPENCATALYST_MODEL_PATH: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None

    # Active learning / retraining triggers
    RETRAIN_TRIGGER_COUNT: int = 10
    RETRAIN_TRIGGER_DRIFT_PSI: float = 0.10

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
