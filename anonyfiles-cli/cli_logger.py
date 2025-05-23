import datetime
import json
import os
from pathlib import Path
import traceback

class CLIUsageLogger:
    LOG_BASE_DIR = Path(__file__).parent / "logs"

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
            print(f"[CLIUsageLogger] Erreur d’écriture log: {e}")

    @classmethod
    def log_error(cls, context: str, exc: Exception):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "context": context
        }
        log_path = cls.get_log_path()
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[CLIUsageLogger] Erreur d’écriture log d’erreur: {e}")

    @classmethod
    def get_last_runs(cls, n=10):
        # Va chercher dans le dossier du jour uniquement (sinon, il faut parcourir tous les sous-dossiers)
        log_path = cls.get_log_path()
        if not log_path.exists():
            return []
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
            return [json.loads(line) for line in lines]
