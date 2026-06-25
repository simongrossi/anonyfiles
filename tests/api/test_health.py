import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient
import importlib
import sys


def get_app():
    sys.modules.setdefault(
        "spacy",
        importlib.util.module_from_spec(importlib.machinery.ModuleSpec("spacy", None)),
    )
    from anonyfiles_api.api import app

    return app


def test_health_endpoint():
    app = get_app()
    app.state.BASE_CONFIG = {"spacy_model": "fr_core_news_md"}
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["spacy"]["model"]["name"] == "fr_core_news_md"
    assert "install_model" in payload["spacy"]["commands"]


def test_spacy_health_endpoint(monkeypatch):
    from anonyfiles_api.routers import health

    monkeypatch.setattr(
        health,
        "get_spacy_status",
        lambda model_name: {
            "status": "missing_model",
            "ready": False,
            "model": {"name": model_name, "installed": False},
            "commands": {"install_model": f"python -m spacy download {model_name}"},
        },
    )

    app = get_app()
    app.state.BASE_CONFIG = {"spacy_model": "custom_model"}
    client = TestClient(app)
    resp = client.get("/health/spacy")

    assert resp.status_code == 200
    assert resp.json()["status"] == "missing_model"
    assert resp.json()["model"]["name"] == "custom_model"
