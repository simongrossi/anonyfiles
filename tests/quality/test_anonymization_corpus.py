import csv
import json
import re
from pathlib import Path

import pytest

pytest.importorskip("spacy")

from anonyfiles_cli.exceptions import ConfigurationError
from anonyfiles_core import AnonyfilesEngine

CORPUS_PATH = Path(__file__).parent / "corpus" / "anonymization_cases.json"

QUALITY_CONFIG = {
    "spacy_model": "fr_core_news_md",
    # LOC/ORG/ADDRESS are covered by explicit custom rules in this corpus.
    # That keeps false-positive expectations stable while the spaCy cleanup remains open.
    "anonymizeLocations": False,
    "anonymizeOrgs": False,
    "anonymizeMisc": False,
    "replacements": {
        "PER": {"type": "redact", "options": {"text": "PER_TOKEN"}},
        "DATE": {"type": "redact", "options": {"text": "DATE_TOKEN"}},
        "EMAIL": {"type": "redact", "options": {"text": "EMAIL_TOKEN"}},
        "PHONE": {"type": "redact", "options": {"text": "PHONE_TOKEN"}},
        "IBAN": {"type": "redact", "options": {"text": "IBAN_TOKEN"}},
        "ADDRESS": {"type": "redact", "options": {"text": "ADDRESS_TOKEN"}},
    },
}


def _load_corpus_cases():
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def _read_mapping_rows(mapping_path: Path):
    with mapping_path.open(encoding="utf-8", newline="") as mapping_file:
        return list(csv.DictReader(mapping_file))


def _assert_no_sensitive_leaks(case_id: str, anonymized_text: str, expectations: dict):
    folded_output = anonymized_text.casefold()

    for literal in expectations.get(
        "sensitive_literals", expectations["absent_literals"]
    ):
        assert (
            literal.casefold() not in folded_output
        ), f"{case_id}: sensitive literal leaked in anonymized output: {literal!r}"

    for pattern in expectations.get("sensitive_patterns", []):
        assert (
            re.search(pattern, anonymized_text, re.IGNORECASE) is None
        ), f"{case_id}: sensitive pattern leaked in anonymized output: {pattern!r}"


@pytest.mark.parametrize(
    "case",
    _load_corpus_cases(),
    ids=lambda case: case["id"],
)
def test_quality_anonymization_corpus(case, tmp_path):
    input_path = tmp_path / f"{case['id']}.txt"
    output_path = tmp_path / f"{case['id']}_anonymized.txt"
    mapping_path = tmp_path / f"{case['id']}_mapping.csv"
    entities_path = tmp_path / f"{case['id']}_entities.csv"

    input_path.write_text(case["input"], encoding="utf-8")

    try:
        engine = AnonyfilesEngine(
            config=QUALITY_CONFIG,
            custom_replacement_rules=case.get("custom_rules", []),
        )
    except ConfigurationError as exc:
        pytest.skip(f"Modele spaCy indisponible pour le corpus qualite: {exc}")

    result = engine.anonymize(
        input_path=input_path,
        output_path=output_path,
        entities=None,
        dry_run=False,
        mapping_output_path=mapping_path,
        log_entities_path=entities_path,
    )

    assert result["status"] == "success", result.get("error")
    assert output_path.exists()
    assert mapping_path.exists()
    assert entities_path.exists()

    anonymized_text = output_path.read_text(encoding="utf-8")
    expectations = case["expect"]

    _assert_no_sensitive_leaks(case["id"], anonymized_text, expectations)

    for literal in expectations["absent_literals"]:
        assert literal not in anonymized_text

    for pattern in expectations.get("absent_patterns", []):
        assert re.search(pattern, anonymized_text) is None

    for literal in expectations["present_literals"]:
        assert literal in anonymized_text

    for literal in expectations["preserved_literals"]:
        assert literal in anonymized_text

    detected_labels = {label for _text, label in result["entities_detected"]}
    for label in expectations["spacy_labels"]:
        assert label in detected_labels

    mapping_rows = _read_mapping_rows(mapping_path)
    rows_by_original = {row["original"]: row for row in mapping_rows}
    for original in expectations["mapping_originals"]:
        assert original in rows_by_original

    for original in expectations["custom_originals"]:
        assert rows_by_original[original]["source"] == "custom_rule"

    assert result["total_replacements"] >= len(expectations["mapping_originals"])
