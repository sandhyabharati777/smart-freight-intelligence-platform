from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Smart Freight Intelligence Platform"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database — use SQLite by default for dev, PostgreSQL for prod
    DATABASE_URL: str = "sqlite+aiosqlite:///./smart_freight.db"
    # Example PostgreSQL: postgresql+asyncpg://user:pass@localhost/smart_freight

    # Redis (optional)
    REDIS_URL: Optional[str] = None  # e.g. "redis://localhost:6379/0"

    # Neo4j (optional)
    NEO4J_URI: Optional[str] = None   # e.g. "bolt://localhost:7687"
    NEO4J_USER: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
