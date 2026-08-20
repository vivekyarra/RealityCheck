import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("REALITYCHECK_STORE", "local")
    monkeypatch.setenv("LOCAL_DB_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
