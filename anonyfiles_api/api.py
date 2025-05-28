# anonyfiles/anonyfiles_api/api.py

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
from pathlib import Path
import shutil
import json
import uuid
import os

# Patch d'import robuste pour Windows/Uvicorn : ajoute le dossier anonyfiles_cli au sys.path AVANT tout import
import sys
sys.path.append(str(Path(__file__).parent.parent / "anonyfiles_cli"))
from anonymizer.run_logger import log_run_event
from cli_logger import CLIUsageLogger
from anonymizer.anonyfiles_core import AnonyfilesEngine
from anonymizer.file_utils import timestamp, default_output, default_mapping, default_log
from main import load_config

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = Path("jobs")
CONFIG_TEMPLATE_PATH = Path(__file__).parent.parent / "anonyfiles_cli" / "config.yaml"

def run_anonymization_job(
    job_id: str,
    input_path: Path,
    config_options: dict,
    has_header: Optional[bool],
    custom_rules: Optional[list]
):
    try:
        print("\n=== [JOB] RÈGLES CUSTOM PASSÉES AU MOTEUR ===")
        print(json.dumps(custom_rules, indent=2, ensure_ascii=False))

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

        output_path = default_output(input_path, input_path.parent, append_timestamp=True)
        log_entities_path = default_log(input_path, input_path.parent)
        mapping_output_path = default_mapping(input_path, input_path.parent)

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

        # Logging centralisé (SUCCESS)
        log_run_event(
            CLIUsageLogger,
            run_id=job_id,
            input_file=str(input_path),
            output_file=str(output_path),
            mapping_file=str(mapping_output_path),
            log_entities_file=str(log_entities_path),
            entities_detected=result.get("entities_detected", []),
            total_replacements=result.get("total_replacements", 0),
            audit_log=result.get("audit_log", []),
            status=result.get("status") or "finished",
            error=result.get("error", None)
        )

        status = {"status": "finished", "error": None}
        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump(status, f)
        with open(input_path.parent / "audit_log.json", "w", encoding="utf-8") as f:
            json.dump(result.get("audit_log", []), f)

    except Exception as e:
        # Logging centralisé (ERREUR)
        log_run_event(
            CLIUsageLogger,
            run_id=job_id,
            input_file=str(input_path),
            output_file=str(output_path if 'output_path' in locals() else ""),
            mapping_file=str(mapping_output_path if 'mapping_output_path' in locals() else ""),
            log_entities_file=str(log_entities_path if 'log_entities_path' in locals() else ""),
            entities_detected=[],
            total_replacements=0,
            audit_log=[],
            status="error",
            error=str(e)
        )
        status = {"status": "error", "error": str(e)}
        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump(status, f)

@app.get("/status")
def status_endpoint():
    return {"status": "ok"}

@app.post("/anonymize/")
async def anonymize_file_endpoint(
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

    print("\n=== [ROUTE] RÈGLES CUSTOM REÇUES ===")
    print(json.dumps(custom_rules, indent=2, ensure_ascii=False))

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
async def anonymize_status_endpoint(job_id: str):
    job_dir = JOBS_DIR / job_id
    status_file = job_dir / "status.json"
    if not status_file.exists():
        return JSONResponse(status_code=404, content={"error": "Job not found"})

    with open(status_file, "r", encoding="utf-8") as f:
        current_status = json.load(f)

    if current_status["status"] == "finished":
        # Sélectionne le fichier le plus récent
        output_candidates = sorted(list(job_dir.glob("*_anonymise_*.*")), key=os.path.getmtime, reverse=True)
        output_file = output_candidates[0] if output_candidates else None

        mapping_candidates = sorted(list(job_dir.glob("*_mapping_*.csv")), key=os.path.getmtime, reverse=True)
        mapping_file = mapping_candidates[0] if mapping_candidates else None

        log_candidates = sorted(list(job_dir.glob("*_entities_*.csv")), key=os.path.getmtime, reverse=True)
        log_file = log_candidates[0] if log_candidates else None

        anonymized_text = output_file.read_text(encoding="utf-8") if output_file and output_file.exists() else ""
        mapping_csv = mapping_file.read_text(encoding="utf-8") if mapping_file and mapping_file.exists() else ""
        log_csv = log_file.read_text(encoding="utf-8") if log_file and log_file.exists() else ""

        audit_log_file = job_dir / "audit_log.json"
        audit_log = []
        if audit_log_file.exists():
            with open(audit_log_file, "r", encoding="utf-8") as f:
                audit_log = json.load(f)

        return {
            "status": "finished",
            "anonymized_text": anonymized_text,
            "mapping_csv": mapping_csv,
            "log_csv": log_csv,
            "audit_log": audit_log,
        }
    elif current_status["status"] == "error":
        return current_status
    else:
        return current_status

@app.get("/files/{job_id}/{file_type}")
async def get_file_endpoint(job_id: str, file_type: str, as_attachment: bool = False):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        return JSONResponse(status_code=404, content={"error": "Job not found"})

    patterns = {
        "output": "*_anonymise_*.*",
        "mapping": "*_mapping_*.csv",
        "log": "*_entities_*.csv",
        "audit": "audit_log.json"
    }

    if file_type not in patterns:
        return JSONResponse(status_code=400, content={"error": "Invalid file_type"})

    pattern = patterns[file_type]
    file_path = None
    if file_type == "audit":
        file_path_candidate = job_dir / pattern
        if file_path_candidate.exists():
             file_path = file_path_candidate
    else:
        matches = sorted(list(job_dir.glob(pattern)), key=lambda p: os.path.getmtime(p) if p.exists() else 0, reverse=True)
        if matches:
            file_path = matches[0]

    if not file_path or not file_path.exists():
        return JSONResponse(status_code=404, content={"error": f"{file_type} file not found for job {job_id} with pattern {pattern}"})

    if as_attachment:
        return FileResponse(str(file_path), filename=file_path.name, media_type="application/octet-stream")
    else:
        return JSONResponse(content={"filename": file_path.name, "content": file_path.read_text(encoding="utf-8")})
