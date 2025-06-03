# anonyfiles_api/api.py

import fastapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import yaml # Importer yaml ici
from typing import Optional, Dict, Any # Pour load_config_for_api

from .routers import anonymization, deanonymization, files, jobs
from .core_config import logger, CONFIG_TEMPLATE_PATH, JOBS_DIR

# Plus besoin d'importer load_config_api_safe depuis anonyfiles_cli.main
# CLI_MODULE_PATH = Path(__file__).resolve().parent.parent / "anonyfiles_cli"
# if str(CLI_MODULE_PATH) not in sys.path:
#     sys.path.append(str(CLI_MODULE_PATH))
# from anonyfiles_cli.main import load_config_api_safe # Supprimer cet import

app = FastAPI(root_path="/api")

JOBS_DIR.mkdir(exist_ok=True)

# Définir la fonction de chargement de configuration ici ou dans core_config.py
def _load_config_for_api(config_path: Path) -> Optional[Dict[str, Any]]:
    """
    Charge un fichier de configuration YAML de manière sécurisée pour l'API.
    Ne termine pas l'application en cas d'erreur mais loggue et retourne None ou {}.
    """
    try:
        if not config_path.is_file():
            logger.error(f"Fichier de configuration '{config_path}' non trouvé.")
            return None # Indique un échec de chargement
        with open(str(config_path), encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            if config_data is None:
                logger.warning(f"Fichier de configuration '{config_path}' est vide ou invalide, chargé comme None. Utilisation de {{}}.")
                return {} # Un YAML vide est valide mais peut être interprété comme None
            if not isinstance(config_data, dict):
                logger.warning(f"Le contenu de '{config_path}' n'est pas un dictionnaire. Type: {type(config_data)}. Utilisation de {{}}.")
                return {}
            return config_data
    except yaml.YAMLError as e:
        logger.error(f"Erreur de parsing YAML dans '{config_path}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du chargement de '{config_path}': {e}", exc_info=True)
        return None

@app.on_event("startup")
async def startup_event():
    try:
        # Utiliser la fonction de chargement définie ci-dessus
        loaded_config = _load_config_for_api(CONFIG_TEMPLATE_PATH) # CONFIG_TEMPLATE_PATH vient de core_config
        
        if loaded_config is None: # Erreur de chargement critique
            logger.error(f"ÉCHEC CRITIQUE du chargement de la configuration depuis {CONFIG_TEMPLATE_PATH}. L'API pourrait ne pas fonctionner. Utilisation d'une config vide {{}}.")
            app.state.BASE_CONFIG = {}
        elif not loaded_config: # Dictionnaire vide (par exemple, YAML vide ou invalide qui a résulté en {})
            logger.warning(f"Configuration de base depuis {CONFIG_TEMPLATE_PATH} est vide. Vérifiez le fichier. Utilisation d'une configuration vide {{}}.")
            app.state.BASE_CONFIG = {} # Ou loaded_config qui est déjà {}
        else:
            app.state.BASE_CONFIG = loaded_config
        
        logger.info(f"Configuration de base chargée dans app.state.BASE_CONFIG. Contient {len(app.state.BASE_CONFIG)} clé(s) au premier niveau.")
        # Pour un debug plus poussé, vous pourriez logger les clés: logger.info(f"Clés: {list(app.state.BASE_CONFIG.keys())}")

    except Exception as e:
        logger.error(f"Erreur critique imprévue DANS L'ÉVÉNEMENT STARTUP lors du chargement de la config: {e}", exc_info=True)
        app.state.BASE_CONFIG = {} # Fallback ultime

# Le reste du fichier (middleware, inclusion des routeurs, endpoint racine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(anonymization.router)
app.include_router(deanonymization.router)
app.include_router(files.router)
app.include_router(jobs.router)

@app.get("/", tags=["Racine"])
async def read_root():
    return {"message": "Bienvenue à l'API Anonyfiles"}