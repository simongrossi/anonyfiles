from types import SimpleNamespace
import uuid

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient


def _get_app():
    from anonyfiles_api.api import app

    return app


class _ApiKeyState:
    def __init__(self, app, api_key: str):
        self.app = app
        self.api_key = api_key
        self.had_settings = hasattr(app.state, "settings")
        self.original_settings = getattr(app.state, "settings", None)

    def __enter__(self):
        self.app.state.settings = SimpleNamespace(api_key=self.api_key)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.had_settings:
            self.app.state.settings = self.original_settings
        else:
            delattr(self.app.state, "settings")


def _missing_job_file_url() -> str:
    return f"/files/{uuid.uuid4()}/output"


def test_auth_disabled_allows_protected_routes_without_key():
    app = _get_app()
    with _ApiKeyState(app, ""):
        client = TestClient(app)
        response = client.get(_missing_job_file_url())

    assert response.status_code == 404


def test_auth_enabled_rejects_missing_key():
    app = _get_app()
    with _ApiKeyState(app, "secret-token"):
        client = TestClient(app)
        response = client.get(_missing_job_file_url())

    assert response.status_code == 401
    assert response.json()["detail"] == "Clé API manquante ou invalide."


def test_auth_enabled_rejects_invalid_key():
    app = _get_app()
    with _ApiKeyState(app, "secret-token"):
        client = TestClient(app)
        response = client.get(
            _missing_job_file_url(),
            headers={"X-API-Key": "wrong-token"},
        )

    assert response.status_code == 401


def test_auth_enabled_accepts_x_api_key():
    app = _get_app()
    with _ApiKeyState(app, "secret-token"):
        client = TestClient(app)
        response = client.get(
            _missing_job_file_url(),
            headers={"X-API-Key": "secret-token"},
        )

    assert response.status_code == 404


def test_auth_enabled_accepts_bearer_token():
    app = _get_app()
    with _ApiKeyState(app, "secret-token"):
        client = TestClient(app)
        response = client.get(
            _missing_job_file_url(),
            headers={"Authorization": "Bearer secret-token"},
        )

    assert response.status_code == 404


def test_root_remains_public_when_auth_is_enabled():
    app = _get_app()
    with _ApiKeyState(app, "secret-token"):
        client = TestClient(app)
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Bienvenue à l'API Anonyfiles"


def test_api_key_is_not_exported_to_core_base_config(monkeypatch):
    monkeypatch.setenv("ANONYFILES_API_KEY", "secret-token")

    from anonyfiles_api.core_config import AppConfig

    settings = AppConfig()
    base_config = settings.model_dump(exclude={"api_key"})

    assert settings.api_key == "secret-token"
    assert "api_key" not in base_config
