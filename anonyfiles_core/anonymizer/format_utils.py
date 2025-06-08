import re

PLACEHOLDER_PATTERN = r"\{\{(?P<tag>[A-Z0-9_]+)_(?P<index>\d+)\}\}"
PLACEHOLDER_REGEX = re.compile(PLACEHOLDER_PATTERN)

ANY_PLACEHOLDER_REGEX = re.compile(r"(\{\{[^{}]+\}\}|\[[^\[\]]+\])")


def create_placeholder(tag: str, index: int, padding: int = 3) -> str:
    """Return a placeholder like ``{{TAG_001}}`` with padded index."""
    index_str = str(index + 1).zfill(padding)
    return f"{{{{{tag}_{index_str}}}}}"


def parse_placeholder(text: str):
    """Parse ``{{TAG_001}}`` style placeholders.

    Returns a tuple ``(tag, index)`` or ``None`` if the text does not
    match the expected pattern.
    """
    match = PLACEHOLDER_REGEX.fullmatch(text)
    if not match:
        return None
    return match.group("tag"), int(match.group("index"))
