from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "MultiModalRAG"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key"

    # Database
    database_url: str = "postgresql://raguser:ragpassword@localhost:5432/ragplatform"
    postgres_user: str = "raguser"
    postgres_password: str = "ragpassword"
    postgres_db: str = "ragplatform"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Vector database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Object storage
    minio_endpoint: str = "http://localhost:9000"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    s3_bucket_name: str = "rag-documents"

    # OpenAI
    openai_api_key: str = "sk-placeholder"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o"
    openai_fallback_model: str = "gpt-4o-mini"

    # JWT
    jwt_secret_key: str = "dev-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"


@lru_cache()
def get_settings() -> Settings:
    return Settings()