from pathlib import Path

from app.config import Settings


def test_vercel_defaults_use_writable_ephemeral_storage(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOCAL_DB_PATH", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "production"
    assert settings.local_db_path == Path("/tmp/realitycheck/realitycheck.sqlite3")
