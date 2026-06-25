from anonyfiles_core.anonymizer.engine import (
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
