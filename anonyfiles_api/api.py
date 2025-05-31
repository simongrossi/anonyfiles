# anonyfiles/anonyfiles_api/api.py

import fastapi
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.concurrency import run_in_threadpool
from typing import Optional, Any
from pathlib import Path
import shutil
import json
import uuid
import os
import logging
import aiofiles
import sys

sys.path.append(str(Path(__file__).parent.parent / "anonyfiles_cli"))
from anonymizer.run_logger import log_run_event
from cli_logger import CLIUsageLogger
from anonymizer.anonyfiles_core import AnonyfilesEngine
from anonymizer.file_utils import timestamp, default_output, default_mapping, default_log
from main import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = Path("jobs")
JOBS_DIR.mkdir(exist_ok=True)
CONFIG_TEMPLATE_PATH = Path(__file__).parent.parent / "anonyfiles_cli" / "config.yaml"

BASE_CONFIG: Optional[dict] = None

@app.on_event("startup")
async def startup_event():
    global BASE_CONFIG
    try:
        BASE_CONFIG = load_config(CONFIG_TEMPLATE_PATH)
        logger.info("Configuration de base chargée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration de base: {e}", exc_info=True)
        BASE_CONFIG = {}

def run_anonymization_job_sync(
    job_id: str,
    input_path: Path,
    config_options: dict,
    has_header: Optional[bool],
    custom_rules: Optional[list]
):
    global BASE_CONFIG
    if BASE_CONFIG is None:
        logger.error(f"Job {job_id}: La configuration de base n'a pas été chargée. Annulation du job.")
        status_file = JOBS_DIR / job_id / "status.json"
        try:
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump({"status": "error", "error": "Base configuration not loaded."}, f)
        except Exception as e_status:
            logger.error(f"Job {job_id}: Impossible d'écrire le statut d'erreur: {e_status}", exc_info=True)
        return

    try:
        logger.info(f"Job {job_id}: Démarrage du traitement d'anonymisation.")
        logger.info(f"Job {job_id}: Règles personnalisées reçues : {custom_rules}")  # <-- Log explicite ici
        logger.debug(f"Job {job_id}: Règles custom passées au moteur: {json.dumps(custom_rules, indent=2, ensure_ascii=False)}")

        exclude_entities = []
        if not config_options.get("anonymizePersons", True): exclude_entities.append("PER")
        if not config_options.get("anonymizeLocations", True): exclude_entities.append("LOC")
        if not config_options.get("anonymizeOrgs", True): exclude_entities.append("ORG")
        if not config_options.get("anonymizeEmails", True): exclude_entities.append("EMAIL")
        if not config_options.get("anonymizeDates", True): exclude_entities.append("DATE")

        output_path = default_output(input_path, input_path.parent, append_timestamp=True)
        log_entities_path = default_log(input_path, input_path.parent)
        mapping_output_path = default_mapping(input_path, input_path.parent)

        engine = AnonyfilesEngine(
            config=BASE_CONFIG,
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
        logger.info(f"Job {job_id}: Anonymisation terminée. Résultat: {result.get('status')}")

        log_run_event(
            CLIUsageLogger, run_id=job_id, input_file=str(input_path),
            output_file=str(output_path), mapping_file=str(mapping_output_path),
            log_entities_file=str(log_entities_path), entities_detected=result.get("entities_detected", []),
            total_replacements=result.get("total_replacements", 0), audit_log=result.get("audit_log", []),
            status=result.get("status") or "finished", error=result.get("error", None)
        )

        status_payload = {"status": "finished", "error": None}
        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump(status_payload, f)
        with open(input_path.parent / "audit_log.json", "w", encoding="utf-8") as f:
            json.dump(result.get("audit_log", []), f)
        logger.info(f"Job {job_id}: Statut et audit log écrits avec succès.")

    except FileNotFoundError as e_fnf:
        logger.error(f"Job {job_id}: Fichier non trouvé lors de l'anonymisation - {e_fnf}", exc_info=True)
        error_message = f"File not found: {e_fnf.filename}"
        status_payload = {"status": "error", "error": error_message}
        log_run_event(CLIUsageLogger, run_id=job_id, input_file=str(input_path), status="error", error=error_message)
    except PermissionError as e_perm:
        logger.error(f"Job {job_id}: Erreur de permission lors de l'anonymisation - {e_perm}", exc_info=True)
        error_message = f"Permission error: {e_perm.strerror} on {e_perm.filename}"
        status_payload = {"status": "error", "error": error_message}
        log_run_event(CLIUsageLogger, run_id=job_id, input_file=str(input_path), status="error", error=error_message)
    except Exception as e:
        logger.error(f"Job {job_id}: Erreur inattendue lors de l'anonymisation - {e}", exc_info=True)
        error_message = f"Unexpected error during anonymization: {str(e)}"
        status_payload = {"status": "error", "error": error_message}
        log_run_event(
            CLIUsageLogger, run_id=job_id, input_file=str(input_path),
            output_file=str(output_path if 'output_path' in locals() else ""),
            mapping_file=str(mapping_output_path if 'mapping_output_path' in locals() else ""),
            log_entities_file=str(log_entities_path if 'log_entities_path' in locals() else ""),
            status="error", error=str(e)
        )
    finally:
        if 'status_payload' in locals() and status_payload.get("status") == "error":
            if input_path and input_path.parent.exists():
                try:
                    with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
                        json.dump(status_payload, f)
                    logger.info(f"Job {job_id}: Statut d'erreur écrit.")
                except Exception as e_status_write:
                    logger.error(f"Job {job_id}: Impossible d'écrire le statut d'erreur final: {e_status_write}", exc_info=True)

@app.post("/anonymize/")
async def anonymize_file_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    config_options: str = Form(...),
    custom_replacement_rules: Optional[str] = Form(None),  # <--- Ajout ici
    file_type: Optional[str] = Form(None),
    has_header: Optional[str] = Form(None)
):
    job_id_obj = uuid.uuid4()
    job_id = str(job_id_obj)
    job_dir = JOBS_DIR / job_id

    logger.info(f"Requête d'anonymisation reçue pour job_id: {job_id}, fichier: {file.filename}")

    try:
        await run_in_threadpool(job_dir.mkdir, parents=True, exist_ok=True)
    except Exception as e_mkdir:
        logger.error(f"Impossible de créer le répertoire du job {job_id}: {e_mkdir}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not create job directory for {job_id}.")

    file_extension = Path(file.filename).suffix
    safe_filename = f"{job_id}{file_extension}"
    input_path = job_dir / safe_filename

    try:
        async with aiofiles.open(input_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        logger.info(f"Job {job_id}: Fichier '{safe_filename}' uploadé avec succès.")
    except Exception as e_upload:
        logger.error(f"Job {job_id}: Erreur lors de l'upload du fichier '{safe_filename}': {e_upload}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file for job {job_id}.")
    finally:
        await file.close()

    initial_status = {"status": "pending", "error": None}
    try:
        async with aiofiles.open(job_dir / "status.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(initial_status))
        logger.info(f"Job {job_id}: Statut initial 'pending' écrit.")
    except Exception as e_status_init:
        logger.error(f"Job {job_id}: Impossible d'écrire le statut initial: {e_status_init}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not write initial status for job {job_id}.")

    try:
        config_opts = json.loads(config_options)
    except json.JSONDecodeError as e_json:
        error_msg = "Invalid JSON format for config_options."
        logger.warning(f"Job {job_id}: {error_msg} - {e_json}", exc_info=True)
        async with aiofiles.open(job_dir / "status.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps({"status": "error", "error": error_msg}))
        raise HTTPException(status_code=400, detail=error_msg)

    custom_rules = None
    if custom_replacement_rules:
        try:
            custom_rules = json.loads(custom_replacement_rules)
        except Exception as e:
            logger.warning(f"Job {job_id}: Erreur parsing custom_replacement_rules : {e}")

    has_header_bool = None
    if has_header is not None:
        has_header_bool = has_header.lower() in ("1", "true", "yes", "on")

    background_tasks.add_task(
        run_anonymization_job_sync,
        job_id=job_id,
        input_path=input_path,
        config_options=config_opts,
        has_header=has_header_bool,
        custom_rules=custom_rules
    )
    logger.info(f"Job {job_id}: Tâche d'anonymisation ajoutée aux tâches de fond.")

    return {"job_id": job_id, "status": "pending"}


@app.get("/anonymize_status/{job_id}")
async def anonymize_status_endpoint(job_id: uuid.UUID):
    job_id_str = str(job_id)
    logger.info(f"Demande de statut pour le job: {job_id_str}")
    job_dir = JOBS_DIR / job_id_str
    status_file = job_dir / "status.json"

    if not await run_in_threadpool(status_file.exists):
        logger.warning(f"Statut du job {job_id_str}: Fichier status.json non trouvé dans {job_dir}.")
        raise HTTPException(status_code=404, detail="Job not found or status file missing.")

    try:
        async with aiofiles.open(status_file, "r", encoding="utf-8") as f:
            content = await f.read()
        current_status = json.loads(content)
        logger.info(f"Statut du job {job_id_str}: {current_status.get('status')}")
    except Exception as e:
        logger.error(f"Statut du job {job_id_str}: Impossible de lire ou parser status.json - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve job status.")

    if current_status["status"] == "finished":
        def get_file_details_sync():
            output_candidates_sync = sorted(
                [p for p in job_dir.glob("*_anonymise_*.*") if p.exists()],
                key=os.path.getmtime, reverse=True
            )
            output_file_sync = output_candidates_sync[0] if output_candidates_sync else None

            mapping_candidates_sync = sorted(
                [p for p in job_dir.glob("*_mapping_*.csv") if p.exists()],
                key=os.path.getmtime, reverse=True
            )
            mapping_file_sync = mapping_candidates_sync[0] if mapping_candidates_sync else None

            log_candidates_sync = sorted(
                [p for p in job_dir.glob("*_entities_*.csv") if p.exists()],
                key=os.path.getmtime, reverse=True
            )
            log_file_sync = log_candidates_sync[0] if log_candidates_sync else None

            return output_file_sync, mapping_file_sync, log_file_sync

        try:
            output_file, mapping_file, log_file = await run_in_threadpool(get_file_details_sync)
        except Exception as e_glob:
            logger.error(f"Job {job_id_str}: Erreur lors de la recherche des fichiers de résultats: {e_glob}", exc_info=True)
            return {"status": "finished", "error": "Could not retrieve result files", "anonymized_text": "", "mapping_csv": "", "log_csv": "", "audit_log": []}

        anonymized_text = ""
        if output_file:
            try:
                async with aiofiles.open(output_file, "r", encoding="utf-8") as f:
                    anonymized_text = await f.read()
            except Exception as e:
                logger.error(f"Job {job_id_str}: Impossible de lire le fichier de sortie {output_file.name} - {e}", exc_info=True)
                current_status["error_output_file"] = f"Could not read output file: {output_file.name}"

        mapping_csv = ""
        if mapping_file:
            try:
                async with aiofiles.open(mapping_file, "r", encoding="utf-8") as f:
                    mapping_csv = await f.read()
            except Exception as e:
                logger.error(f"Job {job_id_str}: Impossible de lire le fichier de mapping {mapping_file.name} - {e}", exc_info=True)
                current_status["error_mapping_file"] = f"Could not read mapping file: {mapping_file.name}"

        log_csv = ""
        if log_file:
            try:
                async with aiofiles.open(log_file, "r", encoding="utf-8") as f:
                    log_csv = await f.read()
            except Exception as e:
                logger.error(f"Job {job_id_str}: Impossible de lire le fichier log entities {log_file.name} - {e}", exc_info=True)
                current_status["error_log_file"] = f"Could not read log entities file: {log_file.name}"

        audit_log: list[Any] = []
        audit_log_file = job_dir / "audit_log.json"
        if await run_in_threadpool(audit_log_file.exists):
            try:
                async with aiofiles.open(audit_log_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                audit_log = json.loads(content)
            except Exception as e:
                logger.error(f"Job {job_id_str}: Impossible de lire ou parser audit_log.json - {e}", exc_info=True)
                current_status["error_audit_log"] = "Could not read audit log file."

        response_payload = {
            "status": "finished",
            "anonymized_text": anonymized_text,
            "mapping_csv": mapping_csv,
            "log_csv": log_csv,
            "audit_log": audit_log,
        }
        if "error_output_file" in current_status: response_payload["error_output_file"] = current_status["error_output_file"]
        if "error_mapping_file" in current_status: response_payload["error_mapping_file"] = current_status["error_mapping_file"]
        if "error_log_file" in current_status: response_payload["error_log_file"] = current_status["error_log_file"]
        if "error_audit_log" in current_status: response_payload["error_audit_log"] = current_status["error_audit_log"]

        return response_payload

    elif current_status["status"] == "error":
        logger.warning(f"Statut du job {job_id_str}: Erreur reportée - {current_status.get('error')}")
        return current_status
    else:
        return current_status

@app.get("/files/{job_id}/{file_type}")
async def get_file_endpoint(job_id: uuid.UUID, file_type: str, as_attachment: bool = False):
    job_id_str = str(job_id)
    logger.info(f"Demande de fichier '{file_type}' pour le job {job_id_str}, as_attachment={as_attachment}")
    job_dir = JOBS_DIR / job_id_str

    if not await run_in_threadpool(job_dir.exists):
        logger.warning(f"Téléchargement de fichier: Job {job_id_str} non trouvé.")
        raise HTTPException(status_code=404, detail="Job not found")

    patterns = {
        "output": "*_anonymise_*.*",
        "mapping": "*_mapping_*.csv",
        "log": "*_entities_*.csv",
        "deanonymized": "*_deanonymise_*.txt",
        "report": "report.json",
        "audit": "audit_log.json"
    }

    if file_type not in patterns:
        logger.warning(f"Téléchargement de fichier: Type de fichier invalide '{file_type}' pour job {job_id_str}.")
        raise HTTPException(status_code=400, detail="Invalid file_type")

    pattern = patterns[file_type]
    file_path: Optional[Path] = None

    def find_file_sync() -> Optional[Path]:
        if file_type in {"audit", "report"}:
            p = job_dir / pattern
            return p if p.exists() else None
        else:
            matches = sorted(
                [p_sync for p_sync in job_dir.glob(pattern) if p_sync.exists()],
                key=os.path.getmtime, reverse=True
            )
            return matches[0] if matches else None

    try:
        file_path = await run_in_threadpool(find_file_sync)
    except Exception as e_find:
        logger.error(f"Job {job_id_str}: Erreur lors de la recherche du fichier '{file_type}': {e_find}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error finding file '{file_type}' for job {job_id_str}")

    if not file_path:
        error_detail = f"{file_type.capitalize()} file not found for job {job_id_str}."
        logger.warning(f"Téléchargement de fichier: {error_detail}")
        raise HTTPException(status_code=404, detail=error_detail)

    logger.info(f"Job {job_id_str}: Service du fichier '{file_path.name}' (type: {file_type}).")
    if as_attachment:
        return FileResponse(str(file_path), filename=file_path.name, media_type="application/octet-stream")
    else:
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content_str = await f.read()

            if file_type in {"audit", "report"}:
                file_content = json.loads(content_str)
            else:
                file_content = content_str

            return JSONResponse(content={"filename": file_path.name, "content": file_content})
        except Exception as e_read_serve:
            logger.error(f"Job {job_id_str}: Erreur lors de la lecture du fichier '{file_path.name}' pour la réponse JSON: {e_read_serve}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Could not read file content for {file_path.name}")
