# anonyfiles_cli/cli_logger.py

import datetime
import json
import logging
from typing import Any, Dict, Optional
import typer
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)


class CLIUsageLogger:
    # Utilisation d'un dossier utilisateur standard pour les logs
    # Linux/Mac: ~/.anonyfiles/logs
    # Windows: C:\Users\Nom\.anonyfiles\logs
    LOG_BASE_DIR = Path.home() / ".anonyfiles" / "logs"
    VERBOSE: bool = False

    @classmethod
    def get_log_path(cls) -> Optional[Path]:
        """Return the path to today's audit log file.

        The method creates the directory structure for the current date if
        it does not already exist and returns the full path to the JSON Lines
        log file used to store CLI audit entries.

        Returns:
            Optional[Path]: Path object to ``cli_audit_log.jsonl``, or None if creation fails.
        """
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            log_dir = (
                cls.LOG_BASE_DIR
                / str(now.year)
                / f"{now.month:02d}"
                / f"{now.day:02d}"
            )
            log_dir.mkdir(parents=True, exist_ok=True)
            return log_dir / "cli_audit_log.jsonl"
        except Exception as e:
            # En cas d'erreur (droits, disque plein...), on loggue discrètement et on retourne None
            # pour ne pas bloquer l'application.
            if cls.VERBOSE:
                logger.warning(
                    "[CLIUsageLogger] Impossible de créer/accéder au dossier de logs: %s", e
                )
            return None

    @classmethod
    def log_run(cls, info: dict):
        """Append a run entry to today's audit log.

        Args:
            info (dict): Arbitrary metadata describing the executed command.
        """
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **info,
        }
        log_path = cls.get_log_path()
        if not log_path:
            return

        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # On ne veut jamais crasher l'appli à cause d'un log auxiliaire
            logger.error("[CLIUsageLogger] Erreur d’écriture log: %s", e)

    @classmethod
    def log_error(
        cls,
        context: str,
        exc: Exception,
        *,
        command: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
    ):
        """Record an error entry in the audit log."""
        entry: Dict[str, Any] = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "context": context,
        }
        if command is not None:
            entry["command"] = command
        if args is not None:
            entry["arguments"] = args
        elif cls.VERBOSE:
            try:
                # Tentative de récupération du contexte Typer si disponible
                ctx = typer.get_current_context()
                entry["command"] = ctx.command_path
                entry["arguments"] = ctx.params
            except Exception:
                pass

        log_path = cls.get_log_path()
        if not log_path:
            return

        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("[CLIUsageLogger] Erreur d’écriture log d’erreur: %s", e)

    @classmethod
    def get_last_runs(cls, n=10):
        """Return the last ``n`` recorded runs from today's log."""
        log_path = cls.get_log_path()
        if not log_path or not log_path.exists():
            return []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # On prend les derniers n lignes valides
                results = []
                for line in reversed(lines):
                    if len(results) >= n:
                        break
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return results[::-1]  # On remet dans l'ordre chronologique
        except Exception as e:
            logger.error("[CLIUsageLogger] Lecture impossible: %s", e)
            return []
