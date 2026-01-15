# anonyfiles/anonymizer/run_logger.py

"""
Module utilitaire pour centraliser le logging des sessions (runs) d'anonymisation
Utilisable aussi bien dans le CLI que l'API pour garantir une structure de log cohérente.
"""

from typing import Any, Dict, Optional


def log_run_event(
    logger: Any,
    run_id: str,
    input_file: str,
    output_file: str,
    mapping_file: str,
    log_entities_file: str,
    entities_detected: Optional[list],
    total_replacements: int,
    audit_log: Optional[list],
    status: str,
    error: Optional[str] = None,
    command: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log une session (run) d'anonymisation/désanonymisation de façon centralisée et cohérente.

    :param logger: Instance de logger (ex : CLIUsageLogger ou autre)
    :param run_id: Identifiant de session (timestamp ou UUID)
    :param input_file: Chemin du fichier source
    :param output_file: Chemin du fichier anonymisé/restauré
    :param mapping_file: Chemin du mapping utilisé/généré
    :param log_entities_file: Chemin du log des entités détectées
    :param entities_detected: Liste des entités détectées
    :param total_replacements: Nombre total de remplacements effectués
    :param audit_log: Log détaillé des règles appliquées (audit)
    :param status: Statut de l'opération ("success", "error", etc.)
    :param error: Message d'erreur éventuel
    """
    logger.log_run(
        {
            "timestamp": run_id,
            "input_file": str(input_file),
            "output_file": str(output_file),
            "mapping_file": str(mapping_file),
            "log_entities_file": str(log_entities_file),
            "entities_detected": entities_detected or [],
            "total_replacements": total_replacements,
            "rules_applied": audit_log or [],
            "success": status == "success",
            "error": error,
            "command": command,
            "arguments": args or {},
        }
    )
