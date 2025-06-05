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
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
