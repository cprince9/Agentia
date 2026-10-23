import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://masds:masds@localhost:5432/masds"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # AWS / S3 / MinIO
    AWS_ACCESS_KEY_ID: str = "minioadmin"
    AWS_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "masds-artifacts"
    S3_ENDPOINT_URL: Optional[str] = "http://localhost:9000"

    # ChromaDB
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8001

    # Security & JWT
    JWT_SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Pipeline Retries & Limits
    MAX_CODER_RETRIES: int = 3
    MAX_REVIEWER_CYCLES: int = 2

    # Sandbox Configuration
    SANDBOX_TIMEOUT_SECONDS: int = 60
    SANDBOX_MEMORY_LIMIT: str = "512m"
    SANDBOX_CPU_LIMIT: str = "0.5"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings()
