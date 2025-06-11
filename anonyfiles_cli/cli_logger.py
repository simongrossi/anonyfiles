# anonyfiles_cli/cli_logger.py

import datetime
import json
import os
import logging
from typing import Any, Dict
import typer
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)

class CLIUsageLogger:
    LOG_BASE_DIR = Path(__file__).parent / "logs"
    VERBOSE: bool = False

    @classmethod
    def get_log_path(cls):
        now = datetime.datetime.now()
        log_dir = cls.LOG_BASE_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "cli_audit_log.jsonl"

    @classmethod
    def log_run(cls, info: dict):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            **info
        }
        log_path = cls.get_log_path()
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("[CLIUsageLogger] Erreur d’écriture log: %s", e)

    @classmethod
    def log_error(cls, context: str, exc: Exception):
        entry: Dict[str, Any] = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "context": context,
        }
        if cls.VERBOSE:
            try:
                ctx = typer.get_current_context()
                entry["command"] = ctx.command_path
                entry["arguments"] = ctx.params
            except Exception:
                pass
        log_path = cls.get_log_path()
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("[CLIUsageLogger] Erreur d’écriture log d’erreur: %s", e)

    @classmethod
    def get_last_runs(cls, n=10):
        # Va chercher dans le dossier du jour uniquement (sinon, il faut parcourir tous les sous-dossiers)
        log_path = cls.get_log_path()
        if not log_path.exists():
            return []
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
            return [json.loads(line) for line in lines]
