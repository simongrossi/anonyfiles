from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pathlib import Path
import shutil
import os
import json
import uuid  # Pour identifiant unique

# Importation de la logique d'anonymisation
try:
    from anonyfiles.anonyfiles_cli.anonymizer.anonyfiles_core import AnonyfilesEngine
    from anonyfiles.anonyfiles_cli.main import load_config
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "anonyfiles-cli"))
    from anonymizer.anonyfiles_core import AnonyfilesEngine
    from main import load_config

# Import du router deanonymize
from deanonymize_api import router as deanonymize_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du router deanonymization
app.include_router(deanonymize_router)

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
    session_id = str(uuid.uuid4())
    session_dir = TEMP_FILES_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        input_path = session_dir / file.filename
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

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
        output_path = session_dir / output_file_name
        log_entities_path = session_dir / f"log_{file.filename}.csv"
        mapping_output_path = session_dir / f"mapping_{file.filename}.csv"

        custom_rules = None
        if "custom_replacement_rules" in frontend_config_options:
            custom_rules = frontend_config_options["custom_replacement_rules"]

        engine = AnonyfilesEngine(
            config=base_config,
            exclude_entities_cli=exclude_entities,
            custom_replacement_rules=custom_rules
        )

        result = engine.anonymize(
            input_path=input_path,
            output_path=output_path,
            entities=None,
            dry_run=False,
            log_entities_path=log_entities_path,
            mapping_output_path=mapping_output_path,
            custom_rules=custom_rules,
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
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)
