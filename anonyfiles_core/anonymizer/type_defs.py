from typing import Any, TypeAlias, TypedDict

TextBlock: TypeAlias = str
TextBlocks: TypeAlias = list[TextBlock]
Entity: TypeAlias = tuple[str, str]
EntitySpan: TypeAlias = tuple[str, str, int, int]
EntitySpansByBlock: TypeAlias = list[list[EntitySpan]]
ReplacementMap: TypeAlias = dict[str, str]
ProcessorKwargs: TypeAlias = dict[str, Any]
JsonPathSegment: TypeAlias = str | int
JsonPath: TypeAlias = list[JsonPathSegment]


class AuditEntry(TypedDict, total=False):
    pattern: str
    replacement: str
    type: str
    count: int
    original_text_for_custom_rule: str


class EngineResult(TypedDict, total=False):
    status: str
    message: str
    error: str
    audit_log: list[AuditEntry]
    total_replacements: int
    entities_detected: list[Entity]
    output_path: str | None
    replacements_applied_spacy: ReplacementMap | None


class ProcessContentResult(TypedDict, total=False):
    decision: str
    blocks_after_custom: TextBlocks
    final_blocks: TextBlocks
    unique_spacy_entities: list[Entity]
    spacy_entities_per_block: EntitySpansByBlock
    replacements_map_spacy: ReplacementMap
    mapping_dict_spacy: ReplacementMap


class SpacyStatusPayload(TypedDict):
    status: str
    ready: bool
    message: str
    python_version: str
    spacy: dict[str, Any]
    model: dict[str, Any]
    commands: dict[str, str]


class ExcelSheetMetadata(TypedDict):
    shape: tuple[int, int]
    index: Any
    columns: Any
