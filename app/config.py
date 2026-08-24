import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_app_env() -> str:
    return "production" if os.getenv("VERCEL") else "development"


def _default_local_db_path() -> Path:
    if os.getenv("VERCEL"):
        return Path("/tmp/realitycheck/realitycheck.sqlite3")
    return Path(".realitycheck/realitycheck.sqlite3")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default_factory=_default_app_env)
    app_name: str = "RealityCheck"
    gemini_model: str = "gemini-3.5-flash"
    google_api_key: str | None = Field(default=None, repr=False)
    google_genai_use_vertexai: bool = False
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    firestore_database: str = "(default)"
    google_service_account_json_b64: str | None = Field(default=None, repr=False)
    realitycheck_store: str = "local"
    provider_mode: str = "sandbox"
    tasks_shared_secret: str | None = Field(default=None, repr=False)
    local_db_path: Path = Field(default_factory=_default_local_db_path)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def ai_configured(self) -> bool:
        return bool(
            self.google_api_key or (self.google_genai_use_vertexai and self.google_cloud_project)
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
