from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
import shutil
import os
import json
import uuid

try:
    from anonyfiles.anonyfiles_cli.anonymizer.anonyfiles_core import AnonyfilesEngine
    from anonyfiles.anonyfiles_cli.main import load_config
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "anonyfiles-cli"))
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

JOBS_DIR = Path("jobs")
CONFIG_TEMPLATE_PATH = Path(__file__).parent.parent / "anonyfiles-cli" / "config.yaml"

def run_anonymization_job(
    job_id: str,
    input_path: Path,
    config_options: dict,
    has_header: Optional[bool],
    custom_rules: Optional[list]
):
    try:
        base_config = load_config(CONFIG_TEMPLATE_PATH)
        exclude_entities = []
        if not config_options.get("anonymizePersons", True):
            exclude_entities.append("PER")
        if not config_options.get("anonymizeLocations", True):
            exclude_entities.append("LOC")
        if not config_options.get("anonymizeOrgs", True):
            exclude_entities.append("ORG")
        if not config_options.get("anonymizeEmails", True):
            exclude_entities.append("EMAIL")
        if not config_options.get("anonymizeDates", True):
            exclude_entities.append("DATE")

        output_path = input_path.parent / "result.txt"
        log_entities_path = input_path.parent / "log.csv"
        mapping_output_path = input_path.parent / "mapping.csv"

        engine = AnonyfilesEngine(
            config=base_config,
            exclude_entities_cli=exclude_entities,
            custom_replacement_rules=custom_rules,
        )

        result = engine.anonymize(
            input_path=input_path,
            output_path=output_path,
            entities=None,
            dry_run=False,
            log_entities_path=log_entities_path,
            mapping_output_path=mapping_output_path,
        )

        # Écrire l'état de job terminé et le résultat
        status = {"status": "finished", "error": None}
        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump(status, f)
        with open(input_path.parent / "audit_log.json", "w", encoding="utf-8") as f:
            json.dump(result.get("audit_log", []), f)
    except Exception as e:
        status = {"status": "error", "error": str(e)}
        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump(status, f)

@app.post("/anonymize/")
async def anonymize_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    config_options: str = Form(...),
    file_type: Optional[str] = Form(None),
    has_header: Optional[str] = Form(None)
):
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    input_path = job_dir / file.filename
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    with open(job_dir / "status.json", "w", encoding="utf-8") as f:
        json.dump({"status": "pending", "error": None}, f)

    config_opts = json.loads(config_options)
    custom_rules = config_opts.get("custom_replacement_rules")
    has_header_bool = None
    if has_header is not None:
        has_header_bool = has_header.lower() in ("1", "true", "yes", "on")

    background_tasks.add_task(
        run_anonymization_job,
        job_id=job_id,
        input_path=input_path,
        config_options=config_opts,
        has_header=has_header_bool,
        custom_rules=custom_rules
    )

    return {"job_id": job_id, "status": "pending"}

@app.get("/anonymize_status/{job_id}")
async def anonymize_status(job_id: str):
    job_dir = JOBS_DIR / job_id
    status_file = job_dir / "status.json"
    if not status_file.exists():
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    with open(status_file, "r", encoding="utf-8") as f:
        status = json.load(f)
    if status["status"] == "finished":
        result_file = job_dir / "result.txt"
        audit_log_file = job_dir / "audit_log.json"
        anonymized_text = result_file.read_text(encoding="utf-8") if result_file.exists() else ""
        if audit_log_file.exists():
            with open(audit_log_file, "r", encoding="utf-8") as f:
                audit_log = json.load(f)
        else:
            audit_log = []
        return {
            "status": "finished",
            "anonymized_text": anonymized_text,
            "audit_log": audit_log,
        }
    elif status["status"] == "error":
        return status
    else:
        return status
