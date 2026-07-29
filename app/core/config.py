from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Edu AI Assistant"
    environment: str = "development"
    log_level: str = "INFO"
    cors_allow_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/edu_ai"
    redis_url: str = "redis://localhost:6379/0"

    line_channel_id: str | None = None
    line_channel_secret: str | None = None
    line_channel_access_token: str | None = None
    line_rich_menu_id_th: str | None = None
    line_rich_menu_id_ms: str | None = None
    line_rich_menu_id_en: str | None = None

    active_text_model_provider: str = "mock"
    active_text_model_name: str = "mock-lesson-v1"
    active_embedding_provider: str = "mock"
    active_embedding_model: str = "mock-embedding-v1"
    active_embedding_dimensions: int = 8

    gemini_api_key: str | None = None
    deepseek_api_key: str | None = None
    qwen_api_key: str | None = None

    storage_provider: str = "local"
    local_storage_dir: Path = Path(".local_storage")
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "lesson-files"

    github_repo: str | None = None
    github_token: str | None = None
    github_branch: str = "main"

    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    dev_admin_email: str = "admin@example.com"
    admin_auth_enabled: bool = True
    admin_username: str = "admin"
    admin_password: str | None = None
    admin_role: str = "super_admin"
    admin_school_ids: str = ""
    admin_region_ids: str = ""

    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = Field(default=0.05, ge=0, le=1)
    monthly_budget_usd: float = Field(default=500, ge=0)

    def validate_enabled_provider_keys(self) -> None:
        if self.active_text_model_provider == "gemini" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when Gemini text provider is active.")
        if self.active_text_model_provider == "deepseek" and not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when DeepSeek provider is active.")
        if self.active_text_model_provider == "qwen" and not self.qwen_api_key:
            raise ValueError("QWEN_API_KEY is required when Qwen provider is active.")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_enabled_provider_keys()
    return settings
