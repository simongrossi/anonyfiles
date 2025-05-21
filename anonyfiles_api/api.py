from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path
import shutil
import os
import json

import sys
from pathlib import Path

# ➜ Ajoute anonyfiles-cli au path Python
CLI_PATH = Path(__file__).parent.parent / "anonyfiles-cli"
if str(CLI_PATH) not in sys.path:
    sys.path.insert(0, str(CLI_PATH))

from anonymizer.anonyfiles_core import AnonyfilesEngine
from main import load_config

app = FastAPI()

# ----------- GESTION CORS POUR LE MODE WEB -----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour le dev, tout autoriser. Restreindre en prod !
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------------------

# Chemin pour les fichiers temporaires et la configuration
TEMP_FILES_DIR = Path("anonyfiles_temp_data")
CONFIG_TEMPLATE_PATH = Path(__file__).parent.parent / "anonyfiles-cli" / "config.yaml"

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Anonyfiles API is running"}

@app.post("/anonymize/")
async def anonymize_file(
    file: UploadFile = File(...),
    config_options: str = Form(...),
    file_type: Optional[str] = Form(None),
    has_header: Optional[str] = Form(None),
    custom_replacement_rules: Optional[str] = Form(None)  # <--- supporte custom rules envoyées
):
    try:
        TEMP_FILES_DIR.mkdir(parents=True, exist_ok=True)

        input_path = TEMP_FILES_DIR / file.filename
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Charger la configuration de base depuis config.yaml
        base_config = load_config(CONFIG_TEMPLATE_PATH)
        print("\n==== [API DEBUG] base_config ====")
        print("type:", type(base_config))
        print("content:", base_config)

        # Charger les options de configuration envoyées par le frontend
        frontend_config_options = json.loads(config_options)
        if not isinstance(frontend_config_options, dict):
            raise ValueError(f"Config options should be a dict, got: {type(frontend_config_options)} - {frontend_config_options}")

        print("frontend_config_options:", frontend_config_options)
        print("file_type:", file_type)
        print("has_header (raw):", has_header)

        if isinstance(has_header, list):
            has_header = has_header[0]
        if isinstance(has_header, str):
            has_header = has_header.lower() in ("1", "true", "on", "yes")

        print("has_header (converted):", has_header)

        exclude_entities = []
        if not frontend_config_options.get("anonymizePersons", True):
            exclude_entities.append("PER")
        if not frontend_config_options.get("anonymizeLocations", True):
            exclude_entities.append("LOC")
        if not frontend_config_options.get("anonymizeOrgs", True):
            exclude_entities.append("ORG")
        if not frontend_config_options.get("anonymizeEmails", True):
            exclude_entities.append("EMAIL")
        if not frontend_config_options.get("anonymizeDates", True):
            exclude_entities.append("DATE")

        print("exclude_entities:", exclude_entities)

        # Chemin des fichiers de sortie
        output_file_name = f"anonymized_{file.filename}"
        output_path = TEMP_FILES_DIR / output_file_name
        log_entities_path = TEMP_FILES_DIR / f"log_{file.filename}.csv"
        mapping_output_path = TEMP_FILES_DIR / f"mapping_{file.filename}.csv"

        # --------- Correction critique ici ---------
        if not isinstance(base_config, dict):
            raise ValueError(f"Config loaded is not a dict: {type(base_config)} {base_config}")
        # -------------------------------------------

        # Traiter les règles custom si fournies
        custom_rules = []
        if custom_replacement_rules:
            try:
                custom_rules = json.loads(custom_replacement_rules)
                print("customReplacementRules reçues :", custom_rules)
            except Exception as e:
                print("Erreur de parsing customReplacementRules:", e)
                custom_rules = []

        # Initialiser l'engine d'anonymisation avec custom rules
        engine = AnonyfilesEngine(
            config=base_config,
            exclude_entities_cli=exclude_entities,
            custom_replacement_rules=custom_rules
        )

        # Gestion paramètre CSV header
        processor_kwargs = {}
        if file_type == "csv":
            processor_kwargs["has_header"] = has_header if has_header is not None else True

        result = engine.anonymize(
            input_path=input_path,
            output_path=output_path,
            entities=None,
            dry_run=False,
            log_entities_path=log_entities_path,
            mapping_output_path=mapping_output_path,
            **processor_kwargs
        )

        if result.get("status") == "success":
            with open(output_path, "r", encoding="utf-8") as f:
                anonymized_content = f.read()
            return {"status": "success", "anonymized_text": anonymized_content}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Erreur inconnue lors de l'anonymisation"))

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur du serveur : {str(e)}")
    finally:
        if TEMP_FILES_DIR.exists():
            shutil.rmtree(TEMP_FILES_DIR, ignore_errors=True)
