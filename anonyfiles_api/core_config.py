# anonyfiles_api/core_config.py
import logging
import sys
from pathlib import Path
# from typing import Optional, Dict, Any # Plus nécessaire ici

# Configuration du Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("anonyfiles_api")

# Chemin vers le template de configuration
CONFIG_TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent
    / "anonyfiles_core"
    / "config"
    / "config.yaml"
)

# Répertoire des tâches (Jobs)
JOBS_DIR = Path("jobs")

# Racine pour les noms de fichiers d'entrée d'une tâche
BASE_INPUT_STEM_FOR_JOB_FILES = "input"

# Rate limit applied to all API endpoints
DEFAULT_RATE_LIMIT = "100/minute"
