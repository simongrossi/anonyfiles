import json

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient


def test_anonymize_preview_returns_detected_entities(monkeypatch):
    from anonyfiles_api.api import app
    from anonyfiles_api.routers import anonymization

    captured = {}

    class FakeEngine:
        def __init__(self, config, **kwargs):
            captured["config"] = config
            captured["kwargs"] = kwargs

        def anonymize(self, **kwargs):
            captured["anonymize_kwargs"] = kwargs
            return {
                "status": "success",
                "entities_detected": [("Jean Dupont", "PER"), ("Paris", "LOC")],
                "audit_log": [
                    {
                        "pattern": "Jean Dupont",
                        "replacement": "[PER_1]",
                        "type": "spacy_PER",
                        "count": 1,
                    },
                    {
                        "pattern": "Paris",
                        "replacement": "[LOC_1]",
                        "type": "spacy_LOC",
                        "count": 2,
                    },
                ],
            }

    monkeypatch.setattr(anonymization, "AnonyfilesEngine", FakeEngine)
    app.state.BASE_CONFIG = {"spacy_model": "fake_model"}

    client = TestClient(app)
    response = client.post(
        "/anonymize_preview/",
        files={"file": ("input.txt", b"Jean Dupont vit a Paris.")},
        data={"config_options": json.dumps({"anonymizePersons": True})},
    )

    assert response.status_code == 200
    assert response.json()["entities"] == [
        {"text": "Jean Dupont", "label": "PER", "count": 1, "enabled": True},
        {"text": "Paris", "label": "LOC", "count": 2, "enabled": True},
    ]
    assert captured["anonymize_kwargs"]["dry_run"] is True
    assert captured["anonymize_kwargs"]["output_path"] is None


def test_entity_decisions_are_parsed_for_engine_options():
    from anonyfiles_api.routers.anonymization import (
        _engine_entity_decision_options,
        _parse_entity_decisions,
    )

    decisions = _parse_entity_decisions(
        json.dumps(
            [
                {"text": "Jean Dupont", "label": "PER", "enabled": True},
                {"text": "Paris", "label": "LOC", "enabled": False},
            ]
        )
    )
    ignored_texts, label_overrides = _engine_entity_decision_options(decisions)

    assert ignored_texts == {"Paris"}
    assert label_overrides == {"Jean Dupont": "PER"}


def test_entity_decisions_reject_invalid_labels():
    from anonyfiles_api.routers.anonymization import _parse_entity_decisions

    with pytest.raises(ValueError, match="label invalide"):
        _parse_entity_decisions(
            json.dumps([{"text": "Jean Dupont", "label": "UNKNOWN"}])
        )
