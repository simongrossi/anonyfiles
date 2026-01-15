import pytest

pytest.importorskip("spacy")
from anonyfiles_core.anonymizer.replacer import ReplacementSession


def test_generate_code_defaults():
    session = ReplacementSession()
    assert session._generate_code("PER", 0) == "{{NOM_001}}"
    assert session._generate_code("PER", 1) == "{{NOM_002}}"


def test_generate_replacements_with_rules():
    session = ReplacementSession()
    entities = [
        ("Jean", "PER"),
        ("Jean", "PER"),
        ("ACME", "ORG"),
        ("01/01/2020", "DATE"),
    ]
    rules = {
        "PER": {"type": "codes", "options": {"prefix": "PERS"}},
        "ORG": {"type": "placeholder", "options": {"format": "{{ORGANIZATION:{}}}"}},
        "DATE": {"type": "redact", "options": {"text": "{{DATE_REMOVED}}"}},
    }
    replacements, mapping = session.generate_replacements(entities, rules)
    assert replacements["Jean"] == "{{PERS_001}}"
    assert mapping["Jean"] == "{{PERS_001}}"
    assert replacements["ACME"] == "{ORGANIZATION:ACME}"
    assert replacements["01/01/2020"] == "{{DATE_REMOVED}}"
