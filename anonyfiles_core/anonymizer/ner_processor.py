# anonyfiles_cli/anonymizer/ner_processor.py

import re
import unicodedata
from typing import List, Dict, Tuple, Set
import logging  #

from .spacy_engine import SpaCyEngine
from .spacy_engine import (
    ADDRESS_REGEX,
    DATE_REGEX,
    EMAIL_REGEX,
    IBAN_REGEX,
    PHONE_REGEX,
)

logger = logging.getLogger(__name__)  #

_EXTRA_FRENCH_FIRST_NAMES = {
    "ambre",
}

_SINGLE_NAME_LINE_RE = re.compile(
    r"(?m)^(?P<prefix>[ \t]*)(?P<name>[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{1,40})(?P<suffix>[ \t]*)$"
)
_STRICT_FIRST_NAME_TOKEN_RE = re.compile(
    r"(?<![\w'’-])(?P<name>[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{1,40})(?![\w'’-])"
)
_STRICT_EMAIL_OBFUSCATED_RE = re.compile(
    r"\b[A-Z0-9._%+-]+[ \t]*"
    r"(?:@|\[?[ \t]*(?:at|arobase)[ \t]*\]?)[ \t]*"
    r"[A-Z0-9.-]+[ \t]*"
    r"(?:\.|\[?[ \t]*(?:dot|point)[ \t]*\]?)[ \t]*"
    r"[A-Z]{2,10}\b",
    re.IGNORECASE,
)
_STRICT_PHONE_RE = re.compile(
    r"(?<!\w)(?:\+33|0033|0)[ \t]*(?:\(0\)[ \t]*)?[1-9]"
    r"(?:[ \t./()-]?\d{2}){4}(?!\w)"
)
_STRICT_ADDRESS_RE = re.compile(
    r"(?<!\w)\d{1,4}[ \t]*(?:bis|ter)?[ \t]+"
    r"(?:rue|avenue|av\.?|boulevard|bd|impasse|chemin|route|all[eé]e|place|quai|cours|square)"
    r"[ \t]+(?:d['’]|de[ \t]+|du[ \t]+|des[ \t]+|la[ \t]+|le[ \t]+|l['’])?"
    r"[A-ZÀ-ÖØ-Þa-zà-öø-ÿ0-9'’.-]+"
    r"(?:[ \t]+[A-ZÀ-ÖØ-Þa-zà-öø-ÿ0-9'’.-]+){0,8}"
    r"(?:[ \t]+\d{5}[ \t]+[A-ZÀ-ÖØ-Þa-zà-öø-ÿ'’.-]+(?:[ \t]+[A-ZÀ-ÖØ-Þa-zà-öø-ÿ'’.-]+){0,4})?"
    r"(?=[\n,.;]|$)",
    re.IGNORECASE,
)
_STRICT_UPPERCASE_LINE_RE = re.compile(
    r"(?m)^[ \t]*(?P<value>[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9&._-]{1,14})[ \t]*$"
)
_STRICT_CONTEXT_VALUE_RE = re.compile(
    r"(?im)^[ \t]*(?P<key>nom|pr[eé]nom|contact|client|soci[eé]t[eé]|entreprise|organisation|"
    r"adresse|t[eé]l(?:[eé]phone)?|telephone|mail|email|matricule|dossier|r[eé]f[eé]rence|reference)"
    r"[ \t]*(?:[:=-]|est|=)[ \t]*(?P<value>[^\n;]{2,100})"
)

_STRICT_CONTEXT_LABEL_BY_KEY = {
    "nom": "PER",
    "prenom": "PER",
    "contact": "PER",
    "client": "MISC",
    "societe": "ORG",
    "entreprise": "ORG",
    "organisation": "ORG",
    "adresse": "ADDRESS",
    "tel": "PHONE",
    "telephone": "PHONE",
    "mail": "EMAIL",
    "email": "EMAIL",
    "matricule": "MISC",
    "dossier": "MISC",
    "reference": "MISC",
}


def _normalize_name_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip())
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return without_accents.replace("’", "'").lower()


def _get_faker_french_first_names() -> tuple[str, ...]:
    try:
        from faker.providers.person.fr_FR import Provider as FrenchPersonProvider
    except ImportError:  # pragma: no cover - faker is a project dependency
        return ()

    return tuple(getattr(FrenchPersonProvider, "first_names", ()))


def _load_french_first_names() -> set[str]:
    names = set(_EXTRA_FRENCH_FIRST_NAMES)
    names.update(_normalize_name_key(name) for name in _get_faker_french_first_names())
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


def _add_non_overlapping_entity(
    text: str,
    label: str,
    start: int,
    end: int,
    entities: List[Tuple[str, str, int, int]],
    enabled_labels: Set[str],
) -> None:
    if label not in enabled_labels:
        return

    clean_entity = _trim_entity_span(text, label, start, end)
    if clean_entity is None:
        return

    _ent_text, _ent_label, clean_start, clean_end = clean_entity
    if _overlaps_existing_span(clean_start, clean_end, entities):
        return

    entities.append(clean_entity)


def _fallback_to_misc(label: str, enabled_labels: Set[str]) -> str | None:
    if label in enabled_labels:
        return label
    if "MISC" in enabled_labels:
        return "MISC"
    return None


def _context_label_for_key(key: str, enabled_labels: Set[str]) -> str | None:
    normalized_key = _normalize_name_key(key)
    label = _STRICT_CONTEXT_LABEL_BY_KEY.get(normalized_key)
    if label is None:
        return None
    return _fallback_to_misc(label, enabled_labels)


def _clean_context_value(value: str) -> str:
    return value.strip(" \t:-=.,;()[]{}\"'’")


class NERProcessor:
    """
    Détecte les entités nommées (NER) dans des blocs de texte en utilisant spaCy et des regex additionnelles.
    """

    def __init__(
        self,
        spacy_engine: SpaCyEngine,
        enabled_labels: Set[str],
        excluded_labels: Set[str],
        strict_mode: bool = False,
    ):
        self.spacy_engine = spacy_engine
        self.enabled_labels = enabled_labels
        self.excluded_labels = excluded_labels
        self.strict_mode = strict_mode

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
            "ADDRESS": ADDRESS_REGEX,
        }

        PRIORITY_REGEX_LABELS = {"EMAIL", "DATE", "PHONE", "IBAN", "ADDRESS"}

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
                        flags = re.IGNORECASE if label in {"ADDRESS", "DATE"} else 0
                        for match in re.finditer(
                            pattern,
                            block_text,
                            flags,
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

                if self.strict_mode:
                    self._add_strict_entities(
                        block_text,
                        detected_entities_for_this_block,
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

    def _add_strict_entities(
        self,
        block_text: str,
        entities: List[Tuple[str, str, int, int]],
    ) -> None:
        enabled = self.final_enabled_labels_for_spacy

        for label, pattern in (
            ("EMAIL", _STRICT_EMAIL_OBFUSCATED_RE),
            ("PHONE", _STRICT_PHONE_RE),
            ("ADDRESS", _STRICT_ADDRESS_RE),
        ):
            if label not in enabled:
                continue
            for match in pattern.finditer(block_text):
                _add_non_overlapping_entity(
                    block_text,
                    label,
                    match.start(),
                    match.end(),
                    entities,
                    enabled,
                )

        if "PER" in enabled:
            for match in _STRICT_FIRST_NAME_TOKEN_RE.finditer(block_text):
                name = match.group("name")
                if _normalize_name_key(name) not in FRENCH_FIRST_NAMES:
                    continue
                _add_non_overlapping_entity(
                    block_text,
                    "PER",
                    match.start("name"),
                    match.end("name"),
                    entities,
                    enabled,
                )

        for match in _STRICT_UPPERCASE_LINE_RE.finditer(block_text):
            uppercase_label = _fallback_to_misc("ORG", enabled)
            if uppercase_label is None:
                continue
            _add_non_overlapping_entity(
                block_text,
                uppercase_label,
                match.start("value"),
                match.end("value"),
                entities,
                enabled,
            )

        for match in _STRICT_CONTEXT_VALUE_RE.finditer(block_text):
            context_label = _context_label_for_key(match.group("key"), enabled)
            if context_label is None:
                continue
            value = _clean_context_value(match.group("value"))
            if not value:
                continue
            value_start = match.start("value") + match.group("value").index(value)
            _add_non_overlapping_entity(
                block_text,
                context_label,
                value_start,
                value_start + len(value),
                entities,
                enabled,
            )
