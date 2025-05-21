from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path
import shutil
import os
import json

# Patch sys.path pour garantir les imports CLI/Python hors package
import sys
cli_path = Path(__file__).parent.parent / "anonyfiles-cli"
if str(cli_path) not in sys.path:
    sys.path.insert(0, str(cli_path))

from anonymizer.anonyfiles_core import AnonyfilesEngine
from main import load_config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    has_header: Optional[str] = Form(None)
):
    try:
        TEMP_FILES_DIR.mkdir(parents=True, exist_ok=True)

        input_path = TEMP_FILES_DIR / file.filename
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Charger la config
        base_config = load_config(CONFIG_TEMPLATE_PATH)
        frontend_config_options = json.loads(config_options)

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

        output_file_name = f"anonymized_{file.filename}"
        output_path = TEMP_FILES_DIR / output_file_name
        log_entities_path = TEMP_FILES_DIR / f"log_{file.filename}.csv"
        mapping_output_path = TEMP_FILES_DIR / f"mapping_{file.filename}.csv"

        # Passage des custom rules
        custom_replacement_rules = None
        if "custom_replacement_rules" in frontend_config_options:
            custom_replacement_rules = frontend_config_options["custom_replacement_rules"]

        engine = AnonyfilesEngine(
            config=base_config,
            exclude_entities_cli=exclude_entities,
            custom_replacement_rules=custom_replacement_rules
        )

        result = engine.anonymize(
            input_path=input_path,
            output_path=output_path,
            entities=None,
            dry_run=False,
            log_entities_path=log_entities_path,
            mapping_output_path=mapping_output_path,
            # Autres options si besoin, sinon custom rules déjà dans l'engine
        )

        if result.get("status") == "success":
            with open(output_path, "r", encoding="utf-8") as f:
                anonymized_content = f.read()
            return {
                "status": "success",
                "anonymized_text": anonymized_content,
                "audit_log": result.get("audit_log", []),
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Erreur inconnue lors de l'anonymisation"))

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur du serveur : {str(e)}")
    finally:
        if TEMP_FILES_DIR.exists():
            shutil.rmtree(TEMP_FILES_DIR, ignore_errors=True)
