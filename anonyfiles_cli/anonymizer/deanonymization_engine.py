import logging
from pathlib import Path
from typing import Dict, Any

from .deanonymize import Deanonymizer

logger = logging.getLogger(__name__)


class DeanonymizationEngine:
    """High level engine orchestrating the deanonymization process."""

    def deanonymize(
        self,
        input_path: Path,
        mapping_path: Path,
        permissive: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Run deanonymization and return result information."""
        try:
            deanonymizer = Deanonymizer(str(mapping_path), strict=not permissive)
            if deanonymizer.map_loading_warnings and not deanonymizer.code_to_originals:
                warning_message = (
                    f"Échec critique du chargement du fichier mapping '{mapping_path}'."
                    f" Avertissements: {deanonymizer.map_loading_warnings}"
                )
                return {
                    "status": "error",
                    "error": warning_message,
                    "restored_text": "",
                    "report": {},
                    "warnings": deanonymizer.map_loading_warnings,
                }

            text = input_path.read_text(encoding="utf-8")
            restored_text, report = deanonymizer.deanonymize_text(text, dry_run=dry_run)
            warnings = report.get("warnings_generated_during_deanonymization", [])
            return {
                "status": "success",
                "restored_text": restored_text,
                "report": report,
                "warnings": warnings,
            }
        except Exception as e:
            logger.error("Deanonymization failed", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "restored_text": "",
                "report": {},
                "warnings": [],
            }
