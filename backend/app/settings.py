from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    jwt_secret: str = "change-me"
    initial_admin_email: str = "admin@example.com"
    initial_admin_password: str = "change-me"
    auto_create_initial_admin: bool = False
    database_url: str = "postgresql+asyncpg://xiaozhi:xiaozhi@localhost:5432/xiaozhi_mcp_hub"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    store_backend: str = "memory"

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


settings = Settings()
