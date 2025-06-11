import pytest
pytest.importorskip("spacy")
import importlib
from types import SimpleNamespace
from unittest.mock import patch

from anonyfiles_core.anonymizer import spacy_engine
from anonyfiles_cli.exceptions import ConfigurationError


class DummyModel:
    def __call__(self, text):
        ents = []
        if "Jean" in text:
            ents.append(SimpleNamespace(text="Jean", label_="PER"))
        return SimpleNamespace(ents=ents)


def test_detect_entities_with_regex():
    dummy = DummyModel()
    with patch.object(spacy_engine, "spacy", SimpleNamespace(load=lambda name: dummy)):
        engine = spacy_engine.SpaCyEngine(model="dummy")
        entities = engine.detect_entities("Jean test@example.com 01/01/2020", {"PER", "EMAIL", "DATE"})
    assert ("Jean", "PER") in entities
    assert ("test@example.com", "EMAIL") in entities
    assert ("01/01/2020", "DATE") in entities


def test_load_model_failure_raises_configuration_error():
    def fail_load(name):
        raise OSError("model missing")

    with patch.object(spacy_engine, "spacy", SimpleNamespace(load=fail_load)):
        with pytest.raises(ConfigurationError):
            spacy_engine.SpaCyEngine(model="missing")
