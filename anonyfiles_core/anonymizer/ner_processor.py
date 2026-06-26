# anonyfiles_cli/anonymizer/ner_processor.py

import re
import unicodedata
from typing import List, Dict, Tuple, Set
import logging  #

from .spacy_engine import SpaCyEngine
from .spacy_engine import EMAIL_REGEX, DATE_REGEX, PHONE_REGEX, IBAN_REGEX

logger = logging.getLogger(__name__)  #

try:
    from faker.providers.person.fr_FR import Provider as FrenchPersonProvider
except ImportError:  # pragma: no cover - faker is a project dependency
    FrenchPersonProvider = None


_EXTRA_FRENCH_FIRST_NAMES = {
    "ambre",
}

_SINGLE_NAME_LINE_RE = re.compile(
    r"(?m)^(?P<prefix>[ \t]*)(?P<name>[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{1,40})(?P<suffix>[ \t]*)$"
)


def _normalize_name_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip())
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return without_accents.replace("’", "'").lower()


def _load_french_first_names() -> set[str]:
    names = set(_EXTRA_FRENCH_FIRST_NAMES)
    if FrenchPersonProvider is not None:
        names.update(
            _normalize_name_key(name)
            for name in getattr(FrenchPersonProvider, "first_names", ())
        )
    return names


FRENCH_FIRST_NAMES = _load_french_first_names()


def _trim_entity_span(
    text: str, label: str, start: int, end: int
) -> tuple[str, str, int, int] | None:
    """Return a clean single-line entity span, or None for unsafe spans."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1

    if start >= end:
        return None

    cleaned_text = text[start:end]
    if "\n" in cleaned_text or "\r" in cleaned_text:
        return None

    return cleaned_text, label, start, end


def _overlaps_existing_span(
    start: int, end: int, entities: List[Tuple[str, str, int, int]]
) -> bool:
    return any(
        start < existing_end and end > existing_start
        for *_, existing_start, existing_end in entities
    )


class NERProcessor:
    """
    Détecte les entités nommées (NER) dans des blocs de texte en utilisant spaCy et des regex additionnelles.
    """

    def __init__(
        self,
        spacy_engine: SpaCyEngine,
        enabled_labels: Set[str],
        excluded_labels: Set[str],
    ):
        self.spacy_engine = spacy_engine
        self.enabled_labels = enabled_labels
        self.excluded_labels = excluded_labels

        self.final_enabled_labels_for_spacy = self.enabled_labels - self.excluded_labels
        logger.debug(  #
            "DEBUG (NERProcessor Init): Labels spaCy effectivement activés pour la détection : %s",  #
            self.final_enabled_labels_for_spacy,  #
        )

    def detect_entities_in_blocks(
        self, text_blocks: List[str]
    ) -> Tuple[List[Tuple[str, str]], List[List[Tuple[str, str, int, int]]]]:
        """
        Détecte les entités dans une liste de blocs de texte.
        Retourne :
        1. Une liste de tuples (entity_text, label) de toutes les entités uniques détectées.
        2. Une liste de listes de tuples (entity_text, label, start_char, end_char) par bloc,
           incluant les offsets pour le remplacement positionnel.
        """
        all_unique_entities_across_blocks: Dict[str, Tuple[str, str]] = (
            {}
        )  # {entity_text: (label, source_type)}
        spacy_entities_per_block_with_offsets: List[List[Tuple[str, str, int, int]]] = (
            []
        )

        regex_sources = {
            "EMAIL": EMAIL_REGEX,
            "DATE": DATE_REGEX,
            "PHONE": PHONE_REGEX,
            "IBAN": IBAN_REGEX,
        }

        PRIORITY_REGEX_LABELS = {"EMAIL", "DATE", "PHONE", "IBAN"}

        for block_text in text_blocks:
            detected_entities_for_this_block: List[Tuple[str, str, int, int]] = (
                []
            )  # Cette variable est celle qui est remplie

            if block_text.strip():
                doc = self.spacy_engine.nlp_doc(block_text)

                # 1. Collecter toutes les entités spaCy pertinentes
                for ent in doc.ents:
                    if ent.label_ in self.final_enabled_labels_for_spacy:
                        clean_entity = _trim_entity_span(
                            block_text, ent.label_, ent.start_char, ent.end_char
                        )
                        if clean_entity is not None:
                            detected_entities_for_this_block.append(clean_entity)

                # 2. Collecter toutes les entités Regex pertinentes
                for label, pattern in regex_sources.items():
                    if label in self.final_enabled_labels_for_spacy:
                        for match in re.finditer(
                            pattern, block_text, re.IGNORECASE if label == "DATE" else 0
                        ):
                            clean_entity = _trim_entity_span(
                                block_text, label, match.start(), match.end()
                            )
                            if clean_entity is not None:
                                detected_entities_for_this_block.append(clean_entity)

                if "PER" in self.final_enabled_labels_for_spacy:
                    for match in _SINGLE_NAME_LINE_RE.finditer(block_text):
                        name = match.group("name")
                        if _normalize_name_key(name) not in FRENCH_FIRST_NAMES:
                            continue
                        start, end = match.span("name")
                        if _overlaps_existing_span(
                            start, end, detected_entities_for_this_block
                        ):
                            continue
                        detected_entities_for_this_block.append(
                            (name, "PER", start, end)
                        )

                # 3. Nettoyer et dédupliquer les entités du bloc avec gestion de priorité
                processed_entities_for_this_block: List[Tuple[str, str, int, int]] = []
                best_entities_by_span: Dict[Tuple[int, int], Tuple[str, str]] = {}

                # La variable à trier est bien 'detected_entities_for_this_block'
                detected_entities_for_this_block.sort(key=lambda x: x[2])

                for ent_text, ent_label, start, end in detected_entities_for_this_block:
                    span = (start, end)

                    if span in best_entities_by_span:
                        existing_text, existing_label = best_entities_by_span[span]

                        if (
                            ent_label in PRIORITY_REGEX_LABELS
                            and existing_label not in PRIORITY_REGEX_LABELS
                        ):
                            best_entities_by_span[span] = (ent_text, ent_label)
                    else:
                        best_entities_by_span[span] = (ent_text, ent_label)

                processed_entities_for_this_block = sorted(
                    [
                        (text, label, start, end)
                        for (start, end), (text, label) in best_entities_by_span.items()
                    ],
                    key=lambda x: x[2],
                )

                # Add to the global list of unique entities (for the mapping)
                for ent_text, ent_label, _, _ in processed_entities_for_this_block:
                    is_current_regex_label = ent_label in PRIORITY_REGEX_LABELS

                    if ent_text not in all_unique_entities_across_blocks:
                        all_unique_entities_across_blocks[ent_text] = (
                            ent_label,
                            "initial",
                        )
                    else:
                        existing_label, _ = all_unique_entities_across_blocks[ent_text]
                        is_existing_regex_label = (
                            existing_label in PRIORITY_REGEX_LABELS
                        )

                        if is_current_regex_label and not is_existing_regex_label:
                            all_unique_entities_across_blocks[ent_text] = (
                                ent_label,
                                "regex_override",
                            )

                spacy_entities_per_block_with_offsets.append(
                    processed_entities_for_this_block
                )

        final_unique_entities_list = [
            (text, data[0]) for text, data in all_unique_entities_across_blocks.items()
        ]

        return final_unique_entities_list, spacy_entities_per_block_with_offsets
