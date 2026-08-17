from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PSY OS"
    app_env: str = "development"
    app_url: str = "http://localhost:8000"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    database_url: str = "postgresql+asyncpg://psyos:psyos_dev@localhost:5432/psyos"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_summary_model: str = "gpt-4o-mini"
    openai_insight_model: str = "gpt-4o-mini"
    openai_complex_model: str = "gpt-4o"
    whisper_model: str = "whisper-1"
    ai_enabled: bool = False
    ai_max_requests_per_psychologist_per_day: int = 20
    ai_cache_ttl_hours: int = 24
    whisper_max_minutes: int = 10

    upload_dir: str = "./uploads"
    max_upload_mb: int = 25
    cors_origins: str = "*"
    serve_frontend: bool = True
    frontend_dir: str = "../frontend"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


settings = Settings()
