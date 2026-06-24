import pytest

pytest.importorskip("spacy")
from types import SimpleNamespace
from unittest.mock import patch

from anonyfiles_core.anonymizer import spacy_engine
from anonyfiles_cli.exceptions import ConfigurationError


class DummyRuler:
    """Faux EntityRuler : accepte des patterns sans rien en faire."""

    def add_patterns(self, patterns):
        self.patterns = patterns


class DummyModel:
    """Double réaliste d'un `Language` spaCy.

    Expose `pipe_names` et `add_pipe` comme le vrai objet, pour que le code de
    production puisse les utiliser sans garde défensive.
    """

    def __init__(self):
        self.pipe_names = ["ner"]

    def add_pipe(self, name, before=None):
        self.pipe_names.insert(0, name)
        return DummyRuler()

    def __call__(self, text):
        ents = []
        if "Jean" in text:
            ents.append(SimpleNamespace(text="Jean", label_="PER"))
        return SimpleNamespace(ents=ents)


def _fake_spacy(load):
    """Faux module `spacy` : `util.is_package` + `load`, comme le vrai."""
    return SimpleNamespace(
        util=SimpleNamespace(is_package=lambda name: True),
        load=load,
    )


def test_detect_entities_with_regex():
    spacy_engine._load_spacy_model_cached.cache_clear()
    dummy = DummyModel()
    with patch.object(spacy_engine, "spacy", _fake_spacy(lambda name: dummy)):
        engine = spacy_engine.SpaCyEngine(model="dummy")
        entities = engine.detect_entities(
            "Jean test@example.com 01/01/2020", {"PER", "EMAIL", "DATE"}
        )
    assert ("Jean", "PER") in entities
    assert ("test@example.com", "EMAIL") in entities
    assert ("01/01/2020", "DATE") in entities


def test_load_model_failure_raises_configuration_error():
    spacy_engine._load_spacy_model_cached.cache_clear()

    def fail_load(name):
        raise OSError("model missing")

    with patch.object(spacy_engine, "spacy", _fake_spacy(fail_load)):
        with pytest.raises(ConfigurationError) as exc:
            spacy_engine.SpaCyEngine(model="missing")
    msg = str(exc.value)
    assert "python -m spacy download missing" in msg
