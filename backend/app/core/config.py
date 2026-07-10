from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Course Learning Assistant API"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me", min_length=8)
    access_token_expire_minutes: int = 60 * 24
    password_min_length: int = 8

    database_url: str = "postgresql+asyncpg://course_agent:course_agent@localhost:5432/course_agent"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "course-materials"
    s3_secure: bool = False

    embedding_api_url: str | None = None
    embedding_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    embedding_batch_size: int = 32

    worker_queue_name: str = "course_agent:jobs"
    worker_retry_queue_name: str = "course_agent:jobs:retry"
    worker_max_retries: int = 3
    worker_poll_timeout_seconds: int = 5

    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="COURSE_AGENT_",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
