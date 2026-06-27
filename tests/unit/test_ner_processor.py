from dataclasses import dataclass

from anonyfiles_core.anonymizer.ner_processor import NERProcessor


@dataclass
class FakeEntity:
    text: str
    label_: str
    start_char: int
    end_char: int


class FakeDoc:
    def __init__(self, entities):
        self.ents = entities


class FakeSpaCyEngine:
    def __init__(self, entities):
        self.entities = entities

    def nlp_doc(self, text):
        return FakeDoc(self.entities)


def test_per_block_offsets_align_with_empty_blocks():
    """Chaque bloc d'entrée doit produire une entrée par-bloc, même vide.

    Les cellules CSV vides créent des blocs vides ; sans liste correspondante,
    l'engine lève `IndexError` en indexant `entities_per_block[i]`.
    """
    processor = NERProcessor(
        FakeSpaCyEngine([]),
        enabled_labels={"PER"},
        excluded_labels=set(),
    )

    blocks = ["Pierre", "", "   ", "Ambre"]
    _unique, per_block = processor.detect_entities_in_blocks(blocks)

    assert len(per_block) == len(blocks)
    assert per_block[1] == []
    assert per_block[2] == []


def test_detects_standalone_french_first_names_as_people():
    processor = NERProcessor(
        FakeSpaCyEngine([]),
        enabled_labels={"PER"},
        excluded_labels=set(),
    )

    unique, per_block = processor.detect_entities_in_blocks(
        ["Alencon\n\nPierre\nAmbre\nJe suis là et tu es la bas\n"]
    )

    assert ("Pierre", "PER") in unique
    assert ("Ambre", "PER") in unique
    assert ("Alencon", "PER") not in unique
    assert ("Pierre", "PER", 9, 15) in per_block[0]
    assert ("Ambre", "PER", 16, 21) in per_block[0]


def test_drops_multiline_entities_and_preserves_trailing_newlines():
    text = "Alencon\n\nPierre\nAmbre\nJe suis là et tu es la bas\n"
    multiline_end = len("Alencon\n\nPierre\n")
    sentence_start = text.index("Je suis")
    entities = [
        FakeEntity("Alencon\n\nPierre\n", "MISC", 0, multiline_end),
        FakeEntity(
            "Je suis là et tu es la bas\n",
            "MISC",
            sentence_start,
            len(text),
        ),
    ]
    processor = NERProcessor(
        FakeSpaCyEngine(entities),
        enabled_labels={"PER", "MISC"},
        excluded_labels=set(),
    )

    unique, per_block = processor.detect_entities_in_blocks([text])

    assert ("Alencon\n\nPierre\n", "MISC") not in unique
    assert ("Je suis là et tu es la bas", "MISC") in unique
    assert (
        "Je suis là et tu es la bas",
        "MISC",
        sentence_start,
        len(text) - 1,
    ) in per_block[0]


def test_detects_conservative_french_addresses():
    processor = NERProcessor(
        FakeSpaCyEngine([]),
        enabled_labels={"ADDRESS"},
        excluded_labels=set(),
    )
    text = (
        "Adresse: 12 Rue Victor-Hugo, 75015 Paris.\n"
        "Note: dossier 12 ouvert par le service RH.\n"
    )
    address = "12 Rue Victor-Hugo, 75015 Paris"

    unique, per_block = processor.detect_entities_in_blocks([text])

    assert (address, "ADDRESS") in unique
    assert ("dossier 12 ouvert", "ADDRESS") not in unique
    assert (
        address,
        "ADDRESS",
        text.index(address),
        text.index(address) + len(address),
    ) in per_block[0]


def test_strict_mode_detects_suspicious_values_missed_by_default():
    text = (
        "Pierre travaille avec Ambre chez KMCL.\n"
        "Contact: ambre [at] exemple [dot] fr\n"
        "Tel: +33 (0)6 12 34 56 78\n"
        "Adresse: 12 rue Victor Hugo 75015 Paris\n"
        "KMCL\n"
    )
    default_processor = NERProcessor(
        FakeSpaCyEngine([]),
        enabled_labels={"PER", "EMAIL", "PHONE", "ADDRESS", "ORG", "MISC"},
        excluded_labels=set(),
    )
    strict_processor = NERProcessor(
        FakeSpaCyEngine([]),
        enabled_labels={"PER", "EMAIL", "PHONE", "ADDRESS", "ORG", "MISC"},
        excluded_labels=set(),
        strict_mode=True,
    )

    default_unique, _ = default_processor.detect_entities_in_blocks([text])
    strict_unique, strict_per_block = strict_processor.detect_entities_in_blocks([text])

    assert ("Pierre", "PER") not in default_unique
    assert ("ambre [at] exemple [dot] fr", "EMAIL") not in default_unique
    assert ("+33 (0)6 12 34 56 78", "PHONE") not in default_unique
    assert ("KMCL", "ORG") not in default_unique

    assert ("Pierre", "PER") in strict_unique
    assert ("Ambre", "PER") in strict_unique
    assert ("ambre [at] exemple [dot] fr", "EMAIL") in strict_unique
    assert ("+33 (0)6 12 34 56 78", "PHONE") in strict_unique
    assert ("12 rue Victor Hugo 75015 Paris", "ADDRESS") in strict_unique
    assert ("KMCL", "ORG") in strict_unique
    assert (
        "ambre [at] exemple [dot] fr",
        "EMAIL",
        text.index("ambre [at]"),
        text.index("ambre [at]") + len("ambre [at] exemple [dot] fr"),
    ) in strict_per_block[0]


def test_strict_mode_still_respects_disabled_labels():
    processor = NERProcessor(
        FakeSpaCyEngine([]),
        enabled_labels={"EMAIL"},
        excluded_labels=set(),
        strict_mode=True,
    )

    unique, _ = processor.detect_entities_in_blocks(
        ["Pierre contacte ambre [at] exemple [dot] fr\nKMCL\n"]
    )

    assert ("ambre [at] exemple [dot] fr", "EMAIL") in unique
    assert ("Pierre", "PER") not in unique
    assert ("KMCL", "ORG") not in unique
