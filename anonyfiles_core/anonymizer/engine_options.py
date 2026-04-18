# anonyfiles_core/anonymizer/engine_options.py
"""Shared helpers for preparing :class:`AnonyfilesEngine` inputs.

The CLI and the HTTP API used to duplicate three chunks of glue code:

* parsing the JSON string of custom replacement rules;
* building the ``exclude_entities_cli`` list from a "toggle dict"
  (``anonymizePersons``, ``anonymizeLocations``, ...);
* building the processor kwargs (``has_header`` for CSV, today).

Keeping the logic here means a fix in the engine contract lands in one
place and both front-ends stay consistent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


# Mapping "toggle key in request" -> "entity label used by the engine".
# Kept as a tuple of tuples so the iteration order is deterministic and the
# callers (tests, logs) see a stable ``exclude_entities`` list.
ENTITY_TOGGLE_MAP: tuple[tuple[str, str], ...] = (
    ("anonymizePersons", "PER"),
    ("anonymizeLocations", "LOC"),
    ("anonymizeOrgs", "ORG"),
    ("anonymizeEmails", "EMAIL"),
    ("anonymizeDates", "DATE"),
    ("anonymizePhones", "PHONE"),
    ("anonymizeIbans", "IBAN"),
    ("anonymizeAddresses", "ADDRESS"),
)


class CustomRulesParseError(ValueError):
    """Raised when a custom-rules JSON payload is syntactically invalid."""


def parse_custom_replacement_rules(
    raw: Optional[str],
    *,
    strict: bool = False,
) -> List[Dict[str, Any]]:
    """Parse a JSON string into a list of custom replacement rule dicts.

    Empty / ``None`` input yields ``[]``. When ``strict`` is true, malformed
    JSON or a non-list payload raises :class:`CustomRulesParseError`; the API
    (historically lenient) calls it with ``strict=False`` so a bad payload
    simply results in "no custom rules", while the CLI can opt into strict
    validation to surface user errors early.
    """

    if raw is None:
        return []
    text = raw.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        if strict:
            raise CustomRulesParseError(
                f"Invalid JSON for custom replacement rules: {exc}"
            ) from exc
        return []

    if not isinstance(parsed, list):
        if strict:
            raise CustomRulesParseError(
                f"Custom replacement rules must be a JSON list, got {type(parsed).__name__}."
            )
        return []

    return parsed


def build_exclude_entities(
    toggles: Mapping[str, Any],
    *,
    has_custom_rules: bool = False,
) -> List[str]:
    """Translate per-entity boolean toggles into an ``exclude_entities`` list.

    A missing key defaults to ``True`` (entity *is* anonymized) which matches
    the pre-existing behavior. ``MISC`` keeps its special default: when custom
    rules are provided, ``anonymizeMisc`` defaults to ``False`` so arbitrary
    misc entities don't get double-processed.
    """

    excluded: List[str] = []
    for toggle_key, entity_label in ENTITY_TOGGLE_MAP:
        if not bool(toggles.get(toggle_key, True)):
            excluded.append(entity_label)

    misc_default = False if has_custom_rules else True
    if not bool(toggles.get("anonymizeMisc", misc_default)):
        excluded.append("MISC")
    return excluded


def build_processor_kwargs(
    input_path: Path,
    *,
    has_header: Optional[bool] = None,
) -> Dict[str, Any]:
    """Build keyword arguments forwarded to the engine's file processor."""
    processor_kwargs: Dict[str, Any] = {}
    if input_path.suffix.lower() == ".csv" and has_header is not None:
        processor_kwargs["has_header"] = has_header
    return processor_kwargs
