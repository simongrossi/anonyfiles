from anonyfiles_core.anonymizer.engine import (
    AnonyfilesEngine,
    add_manual_entities_to_detected_entities,
    apply_entity_decisions_to_detected_entities,
)


def test_apply_entity_decisions_filters_and_overrides_labels():
    unique, per_block = apply_entity_decisions_to_detected_entities(
        [
            [
                ("Jean Dupont", "PER", 0, 11),
                ("Paris", "LOC", 20, 25),
            ],
            [
                ("ACME", "ORG", 0, 4),
            ],
        ],
        ignored_entity_texts={"Paris"},
        entity_label_overrides={"ACME": "MISC"},
    )

    assert unique == [("Jean Dupont", "PER"), ("ACME", "MISC")]
    assert per_block == [
        [("Jean Dupont", "PER", 0, 11)],
        [("ACME", "MISC", 0, 4)],
    ]


def test_add_manual_entities_adds_exact_non_overlapping_spans():
    unique, per_block = add_manual_entities_to_detected_entities(
        ["Projet ACME-Secret avec Jean Dupont et ACME-Secret."],
        [[("Jean Dupont", "PER", 24, 35)]],
        manual_entities=[{"text": "ACME-Secret", "label": "ORG"}],
    )

    assert unique == [("ACME-Secret", "ORG"), ("Jean Dupont", "PER")]
    assert per_block == [
        [
            ("ACME-Secret", "ORG", 7, 18),
            ("Jean Dupont", "PER", 24, 35),
            ("ACME-Secret", "ORG", 39, 50),
        ]
    ]


def test_add_manual_entities_skips_overlapping_detected_spans():
    unique, per_block = add_manual_entities_to_detected_entities(
        ["Ambre Lenoir"],
        [[("Ambre Lenoir", "PER", 0, 12)]],
        manual_entities=[{"text": "Ambre", "label": "PER"}],
    )

    assert unique == [("Ambre Lenoir", "PER")]
    assert per_block == [[("Ambre Lenoir", "PER", 0, 12)]]


def test_engine_manual_entities_are_replaced_when_ner_misses_them(
    monkeypatch, tmp_path
):
    class FakeDoc:
        ents = []

    class FakeSpaCyEngine:
        def __init__(self, model):
            self.model = model

        def nlp_doc(self, text):
            return FakeDoc()

    monkeypatch.setattr(
        "anonyfiles_core.anonymizer.engine.SpaCyEngine", FakeSpaCyEngine
    )
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    mapping_path = tmp_path / "mapping.csv"
    entities_path = tmp_path / "entities.csv"
    input_path.write_text(
        "Projet ACME-Secret à traiter. ACME-Secret est confidentiel.",
        encoding="utf-8",
    )
    engine = AnonyfilesEngine(
        config={
            "spacy_model": "fake",
            "replacements": {
                "ORG": {"type": "redact", "options": {"text": "ORG_TOKEN"}}
            },
        },
        manual_entities=[{"text": "ACME-Secret", "label": "ORG"}],
    )

    result = engine.anonymize(
        input_path=input_path,
        output_path=output_path,
        entities=None,
        dry_run=False,
        log_entities_path=entities_path,
        mapping_output_path=mapping_path,
    )

    assert result["status"] == "success"
    assert "ACME-Secret" not in output_path.read_text(encoding="utf-8")
    assert "ORG_TOKEN_1" in output_path.read_text(encoding="utf-8")
    assert ("ACME-Secret", "ORG") in result["entities_detected"]
    assert result["total_replacements"] == 2
    assert result["privacy_warnings"] == []


def test_engine_strict_mode_replaces_heuristic_entities(monkeypatch, tmp_path):
    class FakeDoc:
        ents = []

    class FakeSpaCyEngine:
        def __init__(self, model):
            self.model = model

        def nlp_doc(self, text):
            return FakeDoc()

    monkeypatch.setattr(
        "anonyfiles_core.anonymizer.engine.SpaCyEngine", FakeSpaCyEngine
    )
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    mapping_path = tmp_path / "mapping.csv"
    entities_path = tmp_path / "entities.csv"
    input_path.write_text(
        "Pierre travaille avec Ambre.\nKMCL\n",
        encoding="utf-8",
    )
    engine = AnonyfilesEngine(
        config={
            "spacy_model": "fake",
            "strict_mode": True,
        },
    )

    result = engine.anonymize(
        input_path=input_path,
        output_path=output_path,
        entities=None,
        dry_run=False,
        log_entities_path=entities_path,
        mapping_output_path=mapping_path,
    )

    output = output_path.read_text(encoding="utf-8")
    assert result["status"] == "success"
    assert "Pierre" not in output
    assert "Ambre" not in output
    assert "KMCL" not in output
    assert ("Pierre", "PER") in result["entities_detected"]
    assert ("Ambre", "PER") in result["entities_detected"]
    assert ("KMCL", "ORG") in result["entities_detected"]


def test_engine_warns_when_suspicious_values_remain_without_changes(
    monkeypatch, tmp_path
):
    class FakeDoc:
        ents = []

    class FakeSpaCyEngine:
        def __init__(self, model):
            self.model = model

        def nlp_doc(self, text):
            return FakeDoc()

    monkeypatch.setattr(
        "anonyfiles_core.anonymizer.engine.SpaCyEngine", FakeSpaCyEngine
    )
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    mapping_path = tmp_path / "mapping.csv"
    entities_path = tmp_path / "entities.csv"
    input_path.write_text("Pierre reste visible.\n", encoding="utf-8")
    engine = AnonyfilesEngine(config={"spacy_model": "fake"})

    result = engine.anonymize(
        input_path=input_path,
        output_path=output_path,
        entities=None,
        dry_run=False,
        log_entities_path=entities_path,
        mapping_output_path=mapping_path,
    )

    assert result["status"] == "success"
    assert result["message"] == "No changes applied"
    assert result["privacy_warnings_count"] == 1
    assert result["privacy_warnings"][0]["kind"] == "FIRST_NAME"
    assert result["privacy_warnings"][0]["examples"] == ["Pierre"]
