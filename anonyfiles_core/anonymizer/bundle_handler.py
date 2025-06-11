import json
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any


def create_bundle(
    bundle_path: Path,
    anonymized_path: Optional[Path],
    mapping_path: Optional[Path],
    audit_log: List[Dict[str, Any]],
    log_entities_path: Optional[Path] = None,
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
