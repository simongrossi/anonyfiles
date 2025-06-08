# anonyfiles_api/core_config.py
import logging
import sys
import os
from pathlib import Path
import contextvars
from pythonjsonlogger import jsonlogger

# Contexte par requête pour le logging
request_context: contextvars.ContextVar[dict] = contextvars.ContextVar(
    "request_context", default={}
)


class RequestContextFilter(logging.Filter):
    """Injecte les informations de contexte dans chaque log."""

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        context = request_context.get({})
        for key in ("endpoint", "client_ip", "job_id"):
            setattr(record, key, context.get(key))
        return True


def set_request_context(endpoint: str, client_ip: str, job_id: str | None = None) -> None:
    request_context.set({"endpoint": endpoint, "client_ip": client_ip, "job_id": job_id})


def set_job_id(job_id: str | None) -> None:
    context = request_context.get({})
    context["job_id"] = job_id
    request_context.set(context)


def clear_request_context() -> None:
    request_context.set({})


handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s %(endpoint)s %(client_ip)s %(job_id)s"
)
handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [handler]
root_logger.addFilter(RequestContextFilter())

logger = logging.getLogger("anonyfiles_api")

# Chemin vers le template de configuration
CONFIG_TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent
    / "anonyfiles_core"
    / "config"
    / "config.yaml"
)

# Répertoire des tâches (Jobs)
JOBS_DIR = Path(os.environ.get("ANONYFILES_JOBS_DIR", "jobs"))

# Racine pour les noms de fichiers d'entrée d'une tâche
BASE_INPUT_STEM_FOR_JOB_FILES = "input"

# Rate limit applied to all API endpoints
DEFAULT_RATE_LIMIT = "100/minute"
