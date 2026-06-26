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
