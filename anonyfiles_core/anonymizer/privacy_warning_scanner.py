import re
from collections.abc import Iterable
from typing import TypedDict

from .ner_processor import FRENCH_FIRST_NAMES, _normalize_name_key
from .spacy_engine import ADDRESS_REGEX, EMAIL_REGEX, IBAN_REGEX, PHONE_REGEX

_MAX_EXAMPLES = 3
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_ -]+}}|\[[A-Z0-9_ -]+]")
_OBFUSCATED_EMAIL_RE = re.compile(
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
_FIRST_NAME_RE = re.compile(
    r"(?<![\w'’-])(?P<name>[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’-]{1,40})(?![\w'’-])"
)
_UPPERCASE_TOKEN_RE = re.compile(r"(?<!\w)[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9&._-]{2,14}(?!\w)")


class _CollectedWarning(TypedDict):
    count: int
    examples: list[str]
    seen: set[str]
    spans: list[tuple[int, int]]


_WARNING_DEFS: dict[str, dict[str, str]] = {
    "EMAIL": {
        "label": "Emails possibles",
        "singular": "email possible",
        "plural": "emails possibles",
        "severity": "high",
    },
    "PHONE": {
        "label": "Téléphones possibles",
        "singular": "téléphone possible",
        "plural": "téléphones possibles",
        "severity": "high",
    },
    "IBAN": {
        "label": "IBAN possibles",
        "singular": "IBAN possible",
        "plural": "IBAN possibles",
        "severity": "high",
    },
    "ADDRESS": {
        "label": "Adresses possibles",
        "singular": "adresse possible",
        "plural": "adresses possibles",
        "severity": "medium",
    },
    "FIRST_NAME": {
        "label": "Prénoms capitalisés possibles",
        "singular": "prénom capitalisé possible",
        "plural": "prénoms capitalisés possibles",
        "severity": "medium",
    },
    "UPPERCASE_TOKEN": {
        "label": "Acronymes ou références en majuscules",
        "singular": "valeur en majuscules possible",
        "plural": "valeurs en majuscules possibles",
        "severity": "low",
    },
}


def scan_blocks_for_privacy_warnings(
    text_blocks: Iterable[str],
    enabled_labels: set[str] | None = None,
    ignored_values: Iterable[str] | None = None,
) -> list[dict[str, object]]:
    enabled = enabled_labels or {
        "PER",
        "ORG",
        "MISC",
        "EMAIL",
        "PHONE",
        "IBAN",
        "ADDRESS",
    }
    ignored = {value for value in (ignored_values or []) if value}
    collector: dict[str, _CollectedWarning] = {}

    for block_text in text_blocks:
        mask_spans = _mask_spans(block_text, ignored)
        _collect_regex_matches(
            collector,
            block_text,
            mask_spans,
            "EMAIL",
            [EMAIL_REGEX, _OBFUSCATED_EMAIL_RE],
            enabled,
        )
        _collect_regex_matches(
            collector,
            block_text,
            mask_spans,
            "PHONE",
            [PHONE_REGEX, _STRICT_PHONE_RE],
            enabled,
        )
        _collect_regex_matches(
            collector,
            block_text,
            mask_spans,
            "IBAN",
            [IBAN_REGEX],
            enabled,
        )
        _collect_regex_matches(
            collector,
            block_text,
            mask_spans,
            "ADDRESS",
            [_STRICT_ADDRESS_RE, ADDRESS_REGEX],
            enabled,
            flags=re.IGNORECASE,
        )
        _collect_first_names(collector, block_text, mask_spans, enabled)
        _collect_uppercase_tokens(collector, block_text, mask_spans, enabled)

    warnings: list[dict[str, object]] = []
    for kind, warning in collector.items():
        count = int(warning["count"])
        definition = _WARNING_DEFS[kind]
        noun = definition["singular"] if count == 1 else definition["plural"]
        warnings.append(
            {
                "kind": kind,
                "label": definition["label"],
                "count": count,
                "examples": warning["examples"],
                "severity": definition["severity"],
                "message": f"Il reste peut-être {count} {noun} dans le résultat.",
            }
        )

    severity_order = {"high": 0, "medium": 1, "low": 2}
    warnings.sort(
        key=lambda item: (
            severity_order.get(str(item["severity"]), 9),
            str(item["label"]),
        )
    )
    return warnings


def privacy_warning_count(warnings: Iterable[dict[str, object]]) -> int:
    total = 0
    for warning in warnings:
        count = warning.get("count", 0)
        if isinstance(count, int):
            total += count
    return total


def _mask_spans(text: str, ignored_values: set[str]) -> list[tuple[int, int]]:
    spans = [(match.start(), match.end()) for match in _PLACEHOLDER_RE.finditer(text)]
    for value in ignored_values:
        for match in re.finditer(re.escape(value), text):
            spans.append((match.start(), match.end()))
    spans.sort()
    return spans


def _is_masked(start: int, end: int, mask_spans: list[tuple[int, int]]) -> bool:
    return any(
        start < mask_end and end > mask_start for mask_start, mask_end in mask_spans
    )


def _add_warning(
    collector: dict[str, _CollectedWarning],
    kind: str,
    value: str,
    span: tuple[int, int] | None = None,
) -> None:
    value = value.strip()
    if not value:
        return

    warning = collector.setdefault(
        kind,
        {"count": 0, "examples": [], "seen": set(), "spans": []},
    )
    spans = warning["spans"]
    if span is not None:
        if any(
            span[0] < existing_end and span[1] > existing_start
            for existing_start, existing_end in spans
        ):
            return
        spans.append(span)

    seen = warning["seen"]
    if value in seen:
        return

    seen.add(value)
    warning["count"] += 1
    examples = warning["examples"]
    if len(examples) < _MAX_EXAMPLES:
        examples.append(value)


def _collect_regex_matches(
    collector: dict[str, _CollectedWarning],
    text: str,
    mask_spans: list[tuple[int, int]],
    kind: str,
    patterns: Iterable[str | re.Pattern[str]],
    enabled_labels: set[str],
    flags: int = 0,
) -> None:
    if kind not in enabled_labels:
        return

    for pattern in patterns:
        matches = (
            pattern.finditer(text)
            if isinstance(pattern, re.Pattern)
            else re.finditer(pattern, text, flags)
        )
        for match in matches:
            if _is_masked(match.start(), match.end(), mask_spans):
                continue
            _add_warning(collector, kind, match.group(0), (match.start(), match.end()))


def _collect_first_names(
    collector: dict[str, _CollectedWarning],
    text: str,
    mask_spans: list[tuple[int, int]],
    enabled_labels: set[str],
) -> None:
    if "PER" not in enabled_labels:
        return

    for match in _FIRST_NAME_RE.finditer(text):
        if _is_masked(match.start("name"), match.end("name"), mask_spans):
            continue
        name = match.group("name")
        if _normalize_name_key(name) in FRENCH_FIRST_NAMES:
            _add_warning(
                collector,
                "FIRST_NAME",
                name,
                (match.start("name"), match.end("name")),
            )


def _collect_uppercase_tokens(
    collector: dict[str, _CollectedWarning],
    text: str,
    mask_spans: list[tuple[int, int]],
    enabled_labels: set[str],
) -> None:
    if "ORG" not in enabled_labels and "MISC" not in enabled_labels:
        return

    for match in _UPPERCASE_TOKEN_RE.finditer(text):
        if _is_masked(match.start(), match.end(), mask_spans):
            continue
        value = match.group(0)
        if any(char.isdigit() for char in value) and len(value) <= 4:
            continue
        _add_warning(
            collector,
            "UPPERCASE_TOKEN",
            value,
            (match.start(), match.end()),
        )
