# anonyfiles_api/core_config.py
import logging
import sys
from pathlib import Path
from contextvars import ContextVar
from typing import Optional

# Configuration du Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("anonyfiles_api")

# ContextVar pour stocker l'ID du job courant (pour logging contextuel futur)
_job_id_ctx: ContextVar[Optional[str]] = ContextVar("job_id", default=None)

# Chemin vers le template de configuration
CONFIG_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "anonyfiles_cli" / "config.yaml"

# Répertoire des tâches (Jobs)
JOBS_DIR = Path("jobs")

# Racine pour les noms de fichiers d'entrée d'une tâche
BASE_INPUT_STEM_FOR_JOB_FILES = "input"

def set_job_id(job_id: Optional[str] = None) -> None:
    """
    Définit l'identifiant de la tâche courante.
    Accepte un ID (str) ou None.
    """
    _job_id_ctx.set(job_id)

def get_job_id() -> Optional[str]:
    """
    Récupère l'identifiant de la tâche courante.
    """
    return _job_id_ctx.get()
