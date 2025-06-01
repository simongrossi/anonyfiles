# anonyfiles/anonyfiles_api/api.py

import fastapi
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, status # Ajout de status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response # Ajout de Response
from fastapi.concurrency import run_in_threadpool
from typing import Optional, Any, Dict, List
from pathlib import Path
import shutil # <--- AJOUTÉ
import json
import uuid
import os
import logging
import aiofiles
import sys

# Assuming deanonymize_api.py is in the same directory (anonyfiles_api)
from . import deanonymize_api

sys.path.append(str(Path(__file__).parent.parent / "anonyfiles_cli"))
from anonymizer.run_logger import log_run_event
from anonyfiles_cli.cli_logger import CLIUsageLogger
from anonymizer.anonyfiles_core import AnonyfilesEngine
from anonymizer.file_utils import timestamp, default_output, default_mapping, default_log
from main import load_config # Assuming 'main' refers to anonyfiles_cli/main.py

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(root_path="/api")

# Include the router from deanonymize_api.py
app.include_router(deanonymize_api.router)

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
BASE_INPUT_STEM_FOR_JOB_FILES = "input"

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

# --- Class Job (Mise à jour avec méthodes d'écriture de statut affinées) ---
class Job:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.job_dir = JOBS_DIR / self.job_id
        self.status_file_path = self.job_dir / "status.json"
        self.audit_log_file_path = self.job_dir / "audit_log.json"
        self.base_input_stem = BASE_INPUT_STEM_FOR_JOB_FILES

    async def check_exists_async(self, check_status_file: bool = True) -> bool:
        dir_exists = await run_in_threadpool(self.job_dir.exists)
        if not dir_exists: return False
        if check_status_file: return await run_in_threadpool(self.status_file_path.exists)
        return True

    async def get_status_async(self) -> Optional[Dict[str, Any]]:
        if not await run_in_threadpool(self.status_file_path.is_file):
            logger.warning(f"Job {self.job_id}: status.json non trouvé pour lecture statut.")
            return None
        try:
            async with aiofiles.open(self.status_file_path, "r", encoding="utf-8") as f:
                content = await f.read()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Job {self.job_id}: Impossible de lire/parser status.json - {e}", exc_info=True)
            return None

    def _find_latest_file_sync(self, glob_suffix_pattern: str) -> Optional[Path]:
        glob_pattern = f"{self.base_input_stem}{glob_suffix_pattern}"
        logger.debug(f"Job {self.job_id}: Recherche fichier {self.job_dir} motif: {glob_pattern}")
        candidates = sorted(
            [p for p in self.job_dir.glob(glob_pattern) if p.is_file()],
            key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates: return candidates[0]
        return None

    def get_file_path_sync(self, file_key: str) -> Optional[Path]:
        if file_key == "output": return self._find_latest_file_sync("_anonymise_*")
        elif file_key == "mapping": return self._find_latest_file_sync("_mapping_*.csv")
        elif file_key == "log_entities": return self._find_latest_file_sync("_entities_*.csv")
        elif file_key == "audit_log":
            p = self.audit_log_file_path
            return p if p.is_file() else None
        logger.warning(f"Job {self.job_id}: Clé fichier inconnue '{file_key}'.")
        return None

    async def read_file_content_async(self, file_path: Path) -> Optional[str]:
        if not await run_in_threadpool(file_path.is_file):
            logger.warning(f"Job {self.job_id}: Tentative lecture fichier inexistant: {file_path}")
            return None
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f: return await f.read()
        except Exception as e:
            logger.error(f"Job {self.job_id}: Erreur lecture fichier {file_path.name}: {e}", exc_info=True)
            return None

    def set_initial_status_sync(self) -> bool:
        try:
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump({"status": "pending", "error": None}, f)
            logger.info(f"Job {self.job_id}: Statut initial 'pending' écrit.")
            return True
        except Exception as e:
            logger.error(f"Job {self.job_id}: Impossible d'écrire statut initial: {e}", exc_info=True)
            return False

    def set_status_as_error_sync(self, error_message: str) -> bool:
        try:
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump({"status": "error", "error": error_message}, f)
            logger.info(f"Job {self.job_id}: Statut d'erreur écrit: {error_message}")
            return True
        except Exception as e:
            logger.error(f"Job {self.job_id}: Impossible d'écrire statut erreur '{error_message}': {e}", exc_info=True)
            return False

    def set_status_as_finished_sync(self, engine_result: Dict[str, Any]) -> bool:
        status_payload = {"status": "finished", "error": None}
        try:
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump(status_payload, f)
            with open(self.audit_log_file_path, "w", encoding="utf-8") as f:
                json.dump(engine_result.get("audit_log", []), f)
            logger.info(f"Job {self.job_id}: Statut 'finished' et audit_log écrits.")
            return True
        except Exception as e:
            logger.error(f"Job {self.job_id}: Impossible d'écrire statut 'finished'/audit_log: {e}", exc_info=True)
            self.set_status_as_error_sync(f"Critical error: Failed to write 'finished' status/audit_log after successful engine run: {str(e)}")
            return False

    # --- NOUVELLE MÉTHODE POUR LA SUPPRESSION ---
    def delete_job_directory_sync(self) -> bool:
        """
        Supprime le répertoire du job et tout son contenu.
        Retourne True en cas de succès, False sinon.
        """
        if not self.job_dir.exists():
            logger.warning(f"Job {self.job_id}: Tentative de suppression d'un répertoire de job inexistant: {self.job_dir}")
            return False # Ou True si l'on considère que l'état désiré (absence du dossier) est atteint

        try:
            shutil.rmtree(self.job_dir)
            logger.info(f"Job {self.job_id}: Répertoire {self.job_dir} supprimé avec succès.")
            return True
        except OSError as e:
            logger.error(f"Job {self.job_id}: Erreur lors de la suppression du répertoire {self.job_dir}: {e}", exc_info=True)
            return False
    # --- FIN DE LA NOUVELLE MÉTHODE ---

# --- Fonctions d'aide pour la logique du job d'anonymisation (adaptées) ---
def _prepare_engine_options(config_options: dict, custom_rules: Optional[list]) -> Dict[str, Any]:
    exclude_entities = []
    if not config_options.get("anonymizePersons", True): exclude_entities.append("PER")
    if not config_options.get("anonymizeLocations", True): exclude_entities.append("LOC")
    if not config_options.get("anonymizeOrgs", True): exclude_entities.append("ORG")
    if not config_options.get("anonymizeEmails", True): exclude_entities.append("EMAIL")
    if not config_options.get("anonymizeDates", True): exclude_entities.append("DATE")
    if not config_options.get("anonymizePhones", True): exclude_entities.append("PHONE")
    if not config_options.get("anonymizeIbans", True): exclude_entities.append("IBAN")
    if not config_options.get("anonymizeAddresses", True): exclude_entities.append("ADDRESS")
    if not config_options.get("anonymizeMisc", True if not custom_rules else False): exclude_entities.append("MISC")
    return {"exclude_entities_cli": exclude_entities, "custom_replacement_rules": custom_rules}

def _prepare_processor_kwargs(input_path: Path, has_header: Optional[bool]) -> Dict[str, Any]:
    processor_kwargs = {}
    if input_path.suffix.lower() == ".csv" and has_header is not None:
        processor_kwargs['has_header'] = has_header
    return processor_kwargs

def _execute_engine_anonymization(
    engine: AnonyfilesEngine, input_path: Path, output_path: Path,
    log_entities_path: Path, mapping_output_path: Path, processor_kwargs: dict
) -> Dict[str, Any]:
    logger.info(f"Job {input_path.parent.name}: Exécution du moteur AnonyfilesEngine.")
    return engine.anonymize(
        input_path=input_path, output_path=output_path, entities=None,
        dry_run=False, log_entities_path=log_entities_path,
        mapping_output_path=mapping_output_path, **processor_kwargs)

def _process_engine_result(
    current_job: Job,
    engine_result: Dict[str, Any],
    input_path: Path,
    output_path: Path,
    mapping_output_path: Path,
    log_entities_path: Path
) -> None: # Ne retourne plus de booléen, le statut est géré via Job
    engine_status_reported = engine_result.get("status")
    engine_error_message = engine_result.get("error")

    final_status_for_log_event: str
    final_error_for_log_event: Optional[str] = None

    if engine_status_reported == "success":
        write_ok = current_job.set_status_as_finished_sync(engine_result)
        final_status_for_log_event = "success" if write_ok else "error"
        if not write_ok:
            final_error_for_log_event = f"Job {current_job.job_id}: Failed to write 'finished' status/audit after successful engine run."
            # current_job.set_status_as_error_sync a déjà été appelé par set_status_as_finished_sync en cas d'échec d'écriture
    else: # "error" ou statut inattendu du moteur
        error_msg_to_set = engine_error_message or f"Engine error or unexpected status: {engine_status_reported}"
        current_job.set_status_as_error_sync(error_msg_to_set)
        final_status_for_log_event = "error"
        final_error_for_log_event = error_msg_to_set

    logger.info(f"Job {current_job.job_id}: Moteur terminé. Statut pour log event: {final_status_for_log_event}, Erreur pour log event: {final_error_for_log_event}")

    log_run_event(
        CLIUsageLogger, run_id=current_job.job_id, input_file=str(input_path),
        output_file=str(output_path), mapping_file=str(mapping_output_path),
        log_entities_file=str(log_entities_path), entities_detected=engine_result.get("entities_detected", []),
        total_replacements=engine_result.get("total_replacements", 0), audit_log=engine_result.get("audit_log", []),
        status=final_status_for_log_event,
        error=final_error_for_log_event
    )

def _handle_job_error(
    current_job: Job,
    e: Exception,
    error_context: str,
    input_path: Path,
    output_path: Optional[Path] = None,
    mapping_output_path: Optional[Path] = None,
    log_entities_path: Optional[Path] = None
) -> None:
    logger.error(f"Job {current_job.job_id}: {error_context} - {e}", exc_info=True)

    if isinstance(e, FileNotFoundError): error_message = f"File not found: {getattr(e, 'filename', 'N/A')}"
    elif isinstance(e, PermissionError): error_message = f"Permission error: {getattr(e, 'strerror', 'N/A')} on {getattr(e, 'filename', 'N/A')}"
    else: error_message = f"Unexpected error during {error_context}: {str(e)}"

    current_job.set_status_as_error_sync(error_message)

    log_run_event(
        CLIUsageLogger, run_id=current_job.job_id, input_file=str(input_path),
        output_file=str(output_path) if output_path else "",
        mapping_file=str(mapping_output_path) if mapping_output_path else "",
        log_entities_file=str(log_entities_path) if log_entities_path else "",
        status="error", error=error_message
    )

def run_anonymization_job_sync(
    job_id: str,
    input_path: Path,
    config_options: dict,
    has_header: Optional[bool],
    custom_rules: Optional[list]
):
    global BASE_CONFIG
    current_job = Job(job_id)
    output_path: Optional[Path] = None
    mapping_output_path: Optional[Path] = None
    log_entities_path: Optional[Path] = None

    if BASE_CONFIG is None:
        logger.error(f"Job {job_id}: Config de base non chargée.")
        try: raise RuntimeError("Base configuration not loaded.")
        except RuntimeError as e_conf: # NOSONAR
            _handle_job_error(current_job, e_conf, "Base config error", input_path)
        return

    try:
        logger.info(f"Job {job_id}: Démarrage pour {input_path.name}. Règles custom: {custom_rules}")
        engine_opts = _prepare_engine_options(config_options, custom_rules)
        processor_kwargs = _prepare_processor_kwargs(input_path, has_header)

        output_path = default_output(input_path, current_job.job_dir, append_timestamp=True)
        log_entities_path = default_log(input_path, current_job.job_dir)
        mapping_output_path = default_mapping(input_path, current_job.job_dir)

        engine = AnonyfilesEngine(config=BASE_CONFIG, **engine_opts)
        engine_result = _execute_engine_anonymization(
            engine, input_path, output_path, log_entities_path, mapping_output_path, processor_kwargs)

        _process_engine_result(
            current_job, engine_result, input_path, output_path, mapping_output_path, log_entities_path
        )
    except FileNotFoundError as e_fnf:
        _handle_job_error(current_job, e_fnf, "File not found", input_path, output_path, mapping_output_path, log_entities_path)
    except PermissionError as e_perm:
        _handle_job_error(current_job, e_perm, "Permission error", input_path, output_path, mapping_output_path, log_entities_path)
    except Exception as e:  # NOSONAR
        _handle_job_error(current_job, e, "Unexpected error during job execution", input_path, output_path, mapping_output_path, log_entities_path)
    finally:
        logger.info(f"Job {job_id}: Traitement de run_anonymization_job_sync terminé.")


@app.post("/anonymize/")
async def anonymize_file_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    config_options: str = Form(...),
    custom_replacement_rules: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None),
    has_header: Optional[str] = Form(None)
):
    job_id = str(uuid.uuid4())
    current_job = Job(job_id)
    job_dir = current_job.job_dir

    logger.info(f"Requête anonymisation job: {job_id}, fichier: {file.filename}, type: {file_type}, header: {has_header}")

    try:
        await run_in_threadpool(job_dir.mkdir, parents=True, exist_ok=True)
    except Exception as e_mkdir: # NOSONAR
        logger.error(f"Impossible créer dir job {job_id}: {e_mkdir}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not create job directory for {job_id}.")

    file_extension = Path(file.filename).suffix if file.filename else ".tmp"
    input_filename_for_job = f"{BASE_INPUT_STEM_FOR_JOB_FILES}{file_extension}"
    input_path_for_job = job_dir / input_filename_for_job

    try:
        async with aiofiles.open(input_path_for_job, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        logger.info(f"Job {job_id}: Fichier '{input_filename_for_job}' (orig: {file.filename}) uploadé.")
    except Exception as e_upload: # NOSONAR
        logger.error(f"Job {job_id}: Erreur upload '{input_filename_for_job}': {e_upload}", exc_info=True)
        # Tenter de marquer le job comme erroné si l'upload échoue.
        await run_in_threadpool(current_job.set_status_as_error_sync, f"Failed to save uploaded file: {str(e_upload)}")
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file for job {job_id}.")
    finally:
        await file.close()

    if not await run_in_threadpool(current_job.set_initial_status_sync):
        logger.error(f"Job {job_id}: Échec écriture statut initial 'pending'.")
        # Ne pas lever d'HTTPException ici, car le job de fond pourrait quand même s'initialiser
        # et écraser ce statut. Le log est important.

    try:
        config_opts_dict = json.loads(config_options)
    except json.JSONDecodeError as e_json_conf:
        error_msg = f"Invalid JSON for config_options: {str(e_json_conf)}"
        logger.error(f"Job {job_id}: {error_msg}", exc_info=True)
        await run_in_threadpool(current_job.set_status_as_error_sync, error_msg + " Config options parsing failed.")
        raise HTTPException(status_code=400, detail=error_msg)

    custom_rules_list = None
    if custom_replacement_rules and custom_replacement_rules.strip():
        try:
            custom_rules_list = json.loads(custom_replacement_rules)
            if not isinstance(custom_rules_list, list):
                logger.warning(f"Job {job_id}: custom_rules n'est pas liste. Reçu: {custom_replacement_rules}. Ignoré.")
                custom_rules_list = None
        except json.JSONDecodeError as e_json_rules: # NOSONAR
            logger.warning(f"Job {job_id}: Erreur parsing custom_rules: {e_json_rules}. Reçu: {custom_replacement_rules}. Ignoré.", exc_info=True)
            custom_rules_list = None

    has_header_bool: Optional[bool] = None
    if has_header is not None:
        has_header_bool = has_header.lower() in ("1", "true", "yes", "on")

    background_tasks.add_task(
        run_anonymization_job_sync, job_id=job_id, input_path=input_path_for_job,
        config_options=config_opts_dict, has_header=has_header_bool, custom_rules=custom_rules_list)
    logger.info(f"Job {job_id}: Tâche de fond ajoutée pour {input_path_for_job}.")

    return {"job_id": job_id, "status": "pending"}


@app.get("/anonymize_status/{job_id}")
async def anonymize_status_endpoint(job_id: uuid.UUID):
    job_id_str = str(job_id)
    current_job = Job(job_id_str)
    logger.info(f"Demande de statut pour job: {job_id_str}")

    if not await current_job.check_exists_async(check_status_file=True):
        logger.warning(f"Statut job {job_id_str}: Fichier status.json ou répertoire job non trouvé.")
        raise HTTPException(status_code=404, detail="Job not found or status file missing.")

    current_status = await current_job.get_status_async()
    if current_status is None:
        # Si get_status_async retourne None, c'est qu'il y a eu un problème pour lire/parser status.json
        # La classe Job aura déjà loggué l'erreur spécifique.
        raise HTTPException(status_code=500, detail="Could not retrieve job status file or it's corrupted.")

    logger.info(f"Statut job {job_id_str} lu depuis status.json: {current_status.get('status')}")

    if current_status.get("status") == "error":
        return JSONResponse(content=current_status)

    if current_status.get("status") == "pending":
        return JSONResponse(content=current_status)

    if current_status.get("status") == "finished":
        response_payload: Dict[str, Any] = {"status": "finished"}
        if "error" in current_status and current_status["error"] is not None :
             response_payload["error"] = current_status["error"]

        response_payload["anonymized_text"] = ""
        response_payload["mapping_csv"] = ""
        response_payload["log_csv"] = ""
        response_payload["audit_log"] = []

        error_details: Dict[str, str] = {}

        try:
            output_file_path = await run_in_threadpool(current_job.get_file_path_sync, "output")
            mapping_file_path = await run_in_threadpool(current_job.get_file_path_sync, "mapping")
            log_entities_file_path = await run_in_threadpool(current_job.get_file_path_sync, "log_entities")
            audit_log_file_path = await run_in_threadpool(current_job.get_file_path_sync, "audit_log")
        except Exception as e_get_paths:  # NOSONAR
            logger.error(f"Job {job_id_str}: Erreur obtention chemins fichiers: {e_get_paths}", exc_info=True)
            response_payload["status"] = "error"
            response_payload["error"] = "Error resolving result file paths for a 'finished' job."
            return JSONResponse(content=response_payload)

        if output_file_path:
            content = await current_job.read_file_content_async(output_file_path)
            if content is not None: response_payload["anonymized_text"] = content
            else: error_details["reading_output_file"] = f"Could not read output file: {output_file_path.name}"
        else: error_details["finding_output_file"] = "Anonymized output file not found."

        if mapping_file_path:
            content = await current_job.read_file_content_async(mapping_file_path)
            if content is not None: response_payload["mapping_csv"] = content
            else: error_details["reading_mapping_file"] = f"Could not read mapping file: {mapping_file_path.name}"

        if log_entities_file_path:
            content = await current_job.read_file_content_async(log_entities_file_path)
            if content is not None: response_payload["log_csv"] = content
            else: error_details["reading_log_file"] = f"Could not read log_entities file: {log_entities_file_path.name}"

        if audit_log_file_path:
            content = await current_job.read_file_content_async(audit_log_file_path)
            if content is not None:
                try: response_payload["audit_log"] = json.loads(content)
                except json.JSONDecodeError: error_details["parsing_audit_log"] = "Could not parse audit_log.json."
            else: error_details["reading_audit_log"] = "Could not read audit_log.json."
        elif not audit_log_file_path:
             error_details["finding_audit_log"] = "Audit log file not found."

        if error_details:
            response_payload.setdefault("error_details", {}).update(error_details)
            if ("reading_output_file" in error_details or "finding_output_file" in error_details) and not response_payload.get("error"):
                 response_payload["error"] = "Failed to retrieve one or more critical result files."

        return JSONResponse(content=response_payload)

    logger.warning(f"Job {job_id_str}: Statut inattendu '{current_status.get('status')}' trouvé dans status.json.")
    return JSONResponse(content=current_status)


@app.get("/files/{job_id}/{file_key}")
async def get_file_endpoint(job_id: uuid.UUID, file_key: str, as_attachment: bool = False):
    job_id_str = str(job_id)
    current_job = Job(job_id_str)
    logger.info(f"Demande fichier clé '{file_key}' pour job {job_id_str}, attachment={as_attachment}")

    if not await current_job.check_exists_async(check_status_file=False):
        logger.warning(f"Téléchargement: Job {job_id_str} non trouvé (répertoire).")
        raise HTTPException(status_code=404, detail="Job directory not found")

    valid_file_keys = {"output", "mapping", "log_entities", "audit_log"}
    if file_key not in valid_file_keys:
        logger.warning(f"Téléchargement: Clé fichier invalide '{file_key}' pour job {job_id_str}.")
        raise HTTPException(status_code=400, detail=f"Invalid file_key. Valid: {', '.join(valid_file_keys)}")

    file_path_to_serve: Optional[Path] = None
    try:
        file_path_to_serve = await run_in_threadpool(current_job.get_file_path_sync, file_key)
    except Exception as e_find:  # NOSONAR
        logger.error(f"Job {job_id_str}: Erreur recherche fichier clé '{file_key}': {e_find}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error finding file for key '{file_key}'.")

    if not file_path_to_serve or not await run_in_threadpool(file_path_to_serve.is_file):
        error_detail = f"{file_key.capitalize()} file not found for job {job_id_str}."
        logger.warning(f"Téléchargement: {error_detail} (Chemin: {file_path_to_serve})")
        raise HTTPException(status_code=404, detail=error_detail)

    logger.info(f"Job {job_id_str}: Service du fichier '{file_path_to_serve.name}' (clé: {file_key}).")

    media_type = "application/octet-stream"
    file_suffix = file_path_to_serve.suffix.lower()

    if file_key in ["mapping", "log_entities"] and file_suffix == ".csv": media_type = "text/csv"
    elif file_key == "output":
        if file_suffix == ".txt": media_type = "text/plain"
        elif file_suffix == ".json": media_type = "application/json"
        elif file_suffix == ".csv": media_type = "text/csv"
        elif file_suffix == ".docx": media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_suffix == ".xlsx": media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif file_suffix == ".pdf": media_type = "application/pdf"
    elif file_key == "audit_log" and file_path_to_serve.name == "audit_log.json": media_type = "application/json" # Nom fixe

    if as_attachment:
        return FileResponse(str(file_path_to_serve), filename=file_path_to_serve.name, media_type=media_type)
    else:
        content = await current_job.read_file_content_async(file_path_to_serve)
        if content is None:
             raise HTTPException(status_code=500, detail=f"Could not read file content for {file_path_to_serve.name}")

        if media_type == "application/json": # Pour audit et output JSON
            try: response_content = json.loads(content)
            except json.JSONDecodeError:  # NOSONAR
                logger.error(f"Job {job_id_str}: Erreur parsing JSON pour {file_path_to_serve.name}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Could not parse JSON content for {file_path_to_serve.name}")
        else: response_content = content # Pour text/plain, text/csv

        return JSONResponse(content={"filename": file_path_to_serve.name, "content": response_content, "media_type": media_type})

# --- NOUVEL ENDPOINT POUR LA SUPPRESSION ---
@app.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_endpoint(job_id: uuid.UUID):
    """
    Supprime un job et tous les fichiers associés (répertoire du job).
    """
    job_id_str = str(job_id)
    current_job = Job(job_id_str)
    logger.info(f"Requête de suppression pour le job ID: {job_id_str}")

    # Vérifier si le répertoire du job existe avant de tenter la suppression
    if not await run_in_threadpool(current_job.job_dir.exists):
        logger.warning(f"Job {job_id_str} non trouvé pour suppression. Répertoire: {current_job.job_dir}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Exécuter la suppression dans un threadpool car shutil.rmtree est bloquant
    deleted_successfully = await run_in_threadpool(current_job.delete_job_directory_sync)

    if not deleted_successfully:
        # Si la suppression a échoué, delete_job_directory_sync a déjà loggué l'erreur.
        # On lève une erreur 500 si le dossier existe toujours (ce qui indiquerait un vrai problème de suppression).
        if await run_in_threadpool(current_job.job_dir.exists):
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete job directory")
        else:
            # Si le dossier n'existe plus (par exemple, il a été supprimé entre la vérification et l'appel,
            # ou delete_job_directory_sync a retourné False mais a quand même réussi à le supprimer),
            # on peut considérer l'opération comme réussie du point de vue du client.
            logger.info(f"Job {job_id_str}: Répertoire non trouvé après tentative de suppression ou déjà supprimé. Opération considérée comme réussie.")
            # Pas besoin de lever d'exception ici, le statut 204 sera renvoyé.

    return Response(status_code=status.HTTP_204_NO_CONTENT)
# --- FIN DU NOUVEL ENDPOINT ---