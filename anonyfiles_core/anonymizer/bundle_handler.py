import json
import zipfile
from pathlib import Path
from typing import Any


def create_bundle(
    bundle_path: Path,
    anonymized_path: Path | None,
    mapping_path: Path | None,
    audit_log: list[dict[str, Any]],
    log_entities_path: Path | None = None,
) -> None:
    """Create a zip archive containing output files and audit log."""
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if anonymized_path and anonymized_path.exists():
            zf.write(anonymized_path, arcname=anonymized_path.name)
        if mapping_path and mapping_path.exists():
            zf.write(mapping_path, arcname=mapping_path.name)
        if log_entities_path and log_entities_path.exists():
            zf.write(log_entities_path, arcname=log_entities_path.name)
        zf.writestr("audit.json", json.dumps(audit_log, ensure_ascii=False, indent=2))
