# anonyfiles_api/api.py

import fastapi
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import yaml # Importer yaml ici
from typing import Optional, Dict, Any # Pour load_config_for_api
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .routers import anonymization, deanonymization, files, jobs, health, websocket_status
from .core_config import (
    logger,
    CONFIG_TEMPLATE_PATH,
    JOBS_DIR,
    DEFAULT_RATE_LIMIT,
    set_request_context,
    clear_request_context,
    set_request_context,
    clear_request_context,
    set_job_id,
    AppConfig,
)

# Plus besoin d'importer load_config_api_safe depuis anonyfiles_cli.main
# CLI_MODULE_PATH = Path(__file__).resolve().parent.parent / "anonyfiles_cli"
# if str(CLI_MODULE_PATH) not in sys.path:
#     sys.path.append(str(CLI_MODULE_PATH))
# from anonyfiles_cli.main import load_config_api_safe # Supprimer cet import

limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_RATE_LIMIT])
app = FastAPI(root_path="/api")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Middleware pour renseigner le contexte de logging
@app.middleware("http")
async def add_logging_context(request: Request, call_next):
    set_request_context(request.url.path, request.client.host if request.client else "unknown")
    try:
        response = await call_next(request)
    finally:
        clear_request_context()
    return response

JOBS_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup_event():
    try:
        # Chargement de la configuration via Pydantic
        # La validation stricte assure que si le YAML est invalide ou corrompu, l'app crashera (Fail Fast)
        logger.info("Chargement et validation de la configuration de l'application...")
        app_config = AppConfig()
        
        # Stocker l'objet config typé (ou convertir en dict si le reste du code attend un dict)
        # Pour compatibilité immédiate avec le code existant qui attend souvent un dict :
        app.state.settings = app_config
        app.state.BASE_CONFIG = app_config.model_dump()
        
        logger.info(f"Configuration validée avec succès via Pydantic Settings.")
        if app_config.debug:
            logger.info("Mode DEBUG activé via la configuration.")

    except Exception as e:
        logger.critical(f"ÉCHEC CRITIQUE: Configuration invalide. L'application ne peut pas démarrer.\nErreur: {e}", exc_info=True)
        # On relève l'exception pour stopper Uvicorn (Fail Fast)
        raise e

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
app.include_router(health.router)
app.include_router(websocket_status.router)

@app.get("/", tags=["Racine"])
async def read_root():
    return {"message": "Bienvenue à l'API Anonyfiles"}
