# anonyfiles_cli/cli_logger.py

import datetime
import json
import os
import logging
from typing import Any, Dict, Optional
import typer
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)

class CLIUsageLogger:
    LOG_BASE_DIR = Path(__file__).parent / "logs"
    VERBOSE: bool = False

    @classmethod
    def get_log_path(cls):
        """Return the path to today's audit log file.

        The method creates the directory structure for the current date if
        it does not already exist and returns the full path to the JSON Lines
        log file used to store CLI audit entries.

        Returns:
            Path: Path object pointing to ``cli_audit_log.jsonl`` for today.
        """
        now = datetime.datetime.now()
        log_dir = cls.LOG_BASE_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "cli_audit_log.jsonl"

    @classmethod
    def log_run(cls, info: dict):
        """Append a run entry to today's audit log.

        Args:
            info (dict): Arbitrary metadata describing the executed command.

        This method automatically adds a UTC timestamp to ``info`` and writes
        it as a JSON object to the log file.
        """
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
    def log_error(
        cls,
        context: str,
        exc: Exception,
        *,
        command: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
    ):
        """Record an error entry in the audit log.

        Args:
            context (str): Text explaining in which context the error occurred.
            exc (Exception): The raised exception instance.
            command (Optional[str], optional): Command name to associate with
                the error. Defaults to ``None``.
            args (Optional[Dict[str, Any]], optional): Parameters passed to the
                command. If ``None`` and ``VERBOSE`` is ``True``, the current
                Typer context is used when available.

        The entry contains the exception message and stack trace in addition to
        the provided context.
        """
        entry: Dict[str, Any] = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
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
        """Return the last ``n`` recorded runs from today's log.

        Only the log file for the current day is inspected; older log files are
        ignored.

        Args:
            n (int): Number of recent entries to retrieve. Defaults to ``10``.

        Returns:
            List[dict]: Parsed log entries ordered from oldest to newest.
        """
        log_path = cls.get_log_path()
        if not log_path.exists():
            return []
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
            return [json.loads(line) for line in lines]
