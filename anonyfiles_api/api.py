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
    has_header: Optional[bool], # Ce paramètre est bien reçu
    custom_rules: Optional[list]
):
    global BASE_CONFIG
    status_payload = {} # Initialisation pour le bloc finally
    output_path = None # Initialisation pour le bloc finally
    mapping_output_path = None # Initialisation pour le bloc finally
    log_entities_path = None # Initialisation pour le bloc finally

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
        logger.info(f"Job {job_id}: Règles personnalisées reçues : {custom_rules}")
        logger.debug(f"Job {job_id}: Règles custom passées au moteur: {json.dumps(custom_rules, indent=2, ensure_ascii=False)}")

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
        
        # --- MODIFICATION 1: Ajout des nouvelles entités ---
        if not config_options.get("anonymizePhones", True):
            exclude_entities.append("PHONE")
        if not config_options.get("anonymizeIbans", True):
            exclude_entities.append("IBAN")
        if not config_options.get("anonymizeAddresses", True):
            exclude_entities.append("ADDRESS")
        # --- FIN MODIFICATION 1 ---

        # Exclure MISC seulement si on a des règles custom ET que l'utilisateur n'a pas coché l'option anonymizeMisc
        # Ou si l'option anonymizeMisc est explicitement false (même sans règles custom)
        if not config_options.get("anonymizeMisc", True if not custom_rules else False): # Anonymise MISC par défaut si pas de règles custom, sinon seulement si coché
             exclude_entities.append("MISC")


        output_path = default_output(input_path, input_path.parent, append_timestamp=True)
        log_entities_path = default_log(input_path, input_path.parent)
        mapping_output_path = default_mapping(input_path, input_path.parent)

        engine = AnonyfilesEngine(
            config=BASE_CONFIG,
            exclude_entities_cli=exclude_entities,
            custom_replacement_rules=custom_rules,
        )

        # --- MODIFICATION 2: Préparation des kwargs pour le moteur ---
        processor_kwargs = {}
        # Typiquement, has_header est pertinent pour les CSV.
        # Vous pourriez étendre cela si d'autres processeurs nécessitent des kwargs spécifiques.
        if input_path.suffix.lower() == ".csv" and has_header is not None:
            processor_kwargs['has_header'] = has_header
        # --- FIN MODIFICATION 2 ---

        result = engine.anonymize(
            input_path=input_path,
            output_path=output_path,
            entities=None,
            dry_run=False,
            log_entities_path=log_entities_path,
            mapping_output_path=mapping_output_path,
            **processor_kwargs  # Passer les kwargs au moteur
        )
        logger.info(f"Job {job_id}: Anonymisation terminée. Résultat: {result.get('status')}")

        # --- MODIFICATION 3: Gestion affinée du status_payload ---
        engine_status = result.get("status")
        engine_error_message = result.get("error")

        if engine_status == "error":
            status_payload = {"status": "error", "error": engine_error_message or "Unknown error from anonymization engine."}
        elif engine_status == "success":
            status_payload = {"status": "finished", "error": None}
        else: # Cas inattendu, considérer comme une erreur
            status_payload = {"status": "error", "error": f"Unexpected engine status: {engine_status}"}
            if engine_error_message:
                 status_payload["error"] += f" - Details: {engine_error_message}"
        # --- FIN MODIFICATION 3 ---

        log_run_event(
            CLIUsageLogger, run_id=job_id, input_file=str(input_path),
            output_file=str(output_path), mapping_file=str(mapping_output_path),
            log_entities_file=str(log_entities_path), entities_detected=result.get("entities_detected", []),
            total_replacements=result.get("total_replacements", 0), audit_log=result.get("audit_log", []),
            status=status_payload["status"], # Utilise le statut du payload
            error=status_payload.get("error") # Utilise l'erreur du payload
        )

        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump(status_payload, f)
        with open(input_path.parent / "audit_log.json", "w", encoding="utf-8") as f:
            json.dump(result.get("audit_log", []), f) # L'audit log peut exister même si erreur partielle
        logger.info(f"Job {job_id}: Statut et audit log écrits avec succès.")

    except FileNotFoundError as e_fnf:
        logger.error(f"Job {job_id}: Fichier non trouvé lors de l'anonymisation - {e_fnf}", exc_info=True)
        error_message = f"File not found: {e_fnf.filename}"
        status_payload = {"status": "error", "error": error_message} # status_payload est défini ici
        log_run_event(CLIUsageLogger, run_id=job_id, input_file=str(input_path), status="error", error=error_message)
    except PermissionError as e_perm:
        logger.error(f"Job {job_id}: Erreur de permission lors de l'anonymisation - {e_perm}", exc_info=True)
        error_message = f"Permission error: {e_perm.strerror} on {e_perm.filename}"
        status_payload = {"status": "error", "error": error_message} # status_payload est défini ici
        log_run_event(CLIUsageLogger, run_id=job_id, input_file=str(input_path), status="error", error=error_message)
    except Exception as e:
        logger.error(f"Job {job_id}: Erreur inattendue lors de l'anonymisation - {e}", exc_info=True)
        error_message = f"Unexpected error during anonymization: {str(e)}"
        status_payload = {"status": "error", "error": error_message} # status_payload est défini ici
        log_run_event(
            CLIUsageLogger, run_id=job_id, input_file=str(input_path),
            output_file=str(output_path if output_path else ""), # output_path peut ne pas être défini
            mapping_file=str(mapping_output_path if mapping_output_path else ""),
            log_entities_file=str(log_entities_path if log_entities_path else ""),
            status="error", error=str(e)
        )
    finally:
        # Ce bloc s'exécute toujours, que le try ait réussi ou échoué.
        # Il est principalement utile pour s'assurer que si une exception a défini status_payload en erreur,
        # ce statut d'erreur est bien écrit dans status.json.
        # Si le try a réussi et a déjà écrit status.json, cette partie pourrait être redondante
        # ou écraser un statut "finished" par un "error" si status_payload a été mal géré plus haut.
        # La logique ci-dessus dans le try/except devrait maintenant correctement définir status_payload.
        if input_path and input_path.parent.exists() and 'status_payload' in locals() and status_payload.get("status") == "error":
            # Écrire status.json seulement si une erreur a été capturée et status_payload est défini en erreur
            try:
                with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
                    json.dump(status_payload, f)
                logger.info(f"Job {job_id}: Statut d'erreur écrit depuis le bloc finally (si applicable).")
            except Exception as e_status_write:
                logger.error(f"Job {job_id}: Impossible d'écrire le statut d'erreur final depuis le bloc finally: {e_status_write}", exc_info=True)


@app.post("/anonymize/")
async def anonymize_file_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    config_options: str = Form(...),
    custom_replacement_rules: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None), # Non utilisé directement par run_anonymization_job_sync mais peut être utile pour le logging ici
    has_header: Optional[str] = Form(None) # Reçu en tant que string
):
    job_id_obj = uuid.uuid4()
    job_id = str(job_id_obj)
    job_dir = JOBS_DIR / job_id

    logger.info(f"Requête d'anonymisation reçue pour job_id: {job_id}, fichier: {file.filename}, file_type: {file_type}, has_header: {has_header}")

    try:
        await run_in_threadpool(job_dir.mkdir, parents=True, exist_ok=True)
    except Exception as e_mkdir:
        logger.error(f"Impossible de créer le répertoire du job {job_id}: {e_mkdir}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not create job directory for {job_id}.")

    file_extension = Path(file.filename).suffix
    safe_filename = f"{job_id}{file_extension}" # Utilise l'extension originale pour input_path
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
        # Ne pas lever d'exception ici permet au job de continuer, le statut d'erreur sera géré par le job lui-même.
        # Mais si le statut initial ne peut pas être écrit, le polling pourrait échouer plus tard.

    try:
        config_opts_dict = json.loads(config_options)
    except json.JSONDecodeError as e_json:
        error_msg = "Invalid JSON format for config_options."
        logger.warning(f"Job {job_id}: {error_msg} - {e_json}", exc_info=True)
        # Écrire l'erreur dans status.json pour que le polling la récupère
        async with aiofiles.open(job_dir / "status.json", "w", encoding="utf-8") as f:
             await f.write(json.dumps({"status": "error", "error": error_msg}))
        # Pas besoin de lever HTTPException ici si le job en arrière-plan peut gérer/reporter cette erreur.
        # Cependant, si config_options est crucial avant même de démarrer le job, une HTTPException est appropriée.
        # Pour l'instant, on laisse le job en arrière-plan le gérer.
        # Mais pour être sûr, on renvoie quand même une réponse HTTP indiquant l'erreur.
        raise HTTPException(status_code=400, detail=error_msg)


    custom_rules_list = None
    if custom_replacement_rules:
        try:
            custom_rules_list = json.loads(custom_replacement_rules)
        except Exception as e:
            logger.warning(f"Job {job_id}: Erreur parsing custom_replacement_rules : {e}. Utilisation de None.")
            # Optionnel : on pourrait aussi faire échouer le job ici si les règles custom sont critiques

    has_header_bool: Optional[bool] = None # Explicitement Optional[bool]
    if has_header is not None:
        has_header_bool = has_header.lower() in ("1", "true", "yes", "on")

    background_tasks.add_task(
        run_anonymization_job_sync,
        job_id=job_id,
        input_path=input_path,
        config_options=config_opts_dict,
        has_header=has_header_bool, # Passer la valeur booléenne ou None
        custom_rules=custom_rules_list
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
        # Il est possible que le job soit encore en train de créer le fichier,
        # ou qu'il y ait eu une erreur très précoce.
        # Renvoyer un statut "pending" ou "not_found" pourrait être plus informatif.
        # Pour l'instant, on garde HTTPException.
        raise HTTPException(status_code=404, detail="Job not found or status file missing.")

    try:
        async with aiofiles.open(status_file, "r", encoding="utf-8") as f:
            content = await f.read()
        current_status = json.loads(content)
        logger.info(f"Statut du job {job_id_str}: {current_status.get('status')}")
    except Exception as e:
        logger.error(f"Statut du job {job_id_str}: Impossible de lire ou parser status.json - {e}", exc_info=True)
        # Si status.json est corrompu ou illisible, c'est une erreur serveur.
        raise HTTPException(status_code=500, detail="Could not retrieve job status.")

    if current_status["status"] == "finished":
        # Logique pour récupérer les chemins des fichiers résultats
        def get_file_details_sync():
            # Recherche du fichier de sortie anonymisé (avec n'importe quelle extension)
            output_candidates_sync = sorted(
                [p for p in job_dir.glob(f"{job_id_str}_anonymise_*") if p.is_file()],
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            output_file_sync = output_candidates_sync[0] if output_candidates_sync else None

            # Recherche du fichier de mapping
            mapping_candidates_sync = sorted(
                [p for p in job_dir.glob(f"{job_id_str}_mapping_*.csv") if p.is_file()],
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            mapping_file_sync = mapping_candidates_sync[0] if mapping_candidates_sync else None

            # Recherche du fichier de log des entités
            log_candidates_sync = sorted(
                [p for p in job_dir.glob(f"{job_id_str}_entities_*.csv") if p.is_file()],
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            log_file_sync = log_candidates_sync[0] if log_candidates_sync else None
            
            return output_file_sync, mapping_file_sync, log_file_sync

        try:
            output_file, mapping_file, log_file = await run_in_threadpool(get_file_details_sync)
        except Exception as e_glob: # Erreur durant la recherche des fichiers
            logger.error(f"Job {job_id_str}: Erreur lors de la recherche des fichiers de résultats: {e_glob}", exc_info=True)
            # Renvoyer le statut "finished" mais avec une erreur indiquant que les résultats sont introuvables
            return {"status": "finished", "error": "Could not retrieve result files after successful anonymization.", "anonymized_text": "", "mapping_csv": "", "log_csv": "", "audit_log": []}


        anonymized_text = ""
        if output_file and await run_in_threadpool(output_file.exists):
            try:
                async with aiofiles.open(output_file, "r", encoding="utf-8") as f:
                    anonymized_text = await f.read()
            except Exception as e: # Erreur de lecture du fichier de sortie
                logger.error(f"Job {job_id_str}: Impossible de lire le fichier de sortie {output_file.name} - {e}", exc_info=True)
                # Ne pas écraser current_status, mais plutôt ajouter une note à la réponse
                current_status["error_reading_output_file"] = f"Could not read output file: {output_file.name}"
        elif not output_file:
            logger.warning(f"Job {job_id_str}: Fichier de sortie non trouvé pour un job 'finished'.")
            current_status["error_reading_output_file"] = "Output file not found for finished job."


        mapping_csv = ""
        if mapping_file and await run_in_threadpool(mapping_file.exists):
            try:
                async with aiofiles.open(mapping_file, "r", encoding="utf-8") as f:
                    mapping_csv = await f.read()
            except Exception as e:
                logger.error(f"Job {job_id_str}: Impossible de lire le fichier de mapping {mapping_file.name} - {e}", exc_info=True)
                current_status["error_reading_mapping_file"] = f"Could not read mapping file: {mapping_file.name}"
        elif not mapping_file:
            logger.warning(f"Job {job_id_str}: Fichier de mapping non trouvé pour un job 'finished'.")
            # Pas critique au point de changer le statut global en "error" si l'output est là.


        log_csv = "" # Le frontend ne l'utilise pas directement dans outputText, auditLog, mappingCSV
                     # Mais on le prépare quand même pour la réponse.
        if log_file and await run_in_threadpool(log_file.exists):
            try:
                async with aiofiles.open(log_file, "r", encoding="utf-8") as f:
                    log_csv = await f.read()
            except Exception as e:
                logger.error(f"Job {job_id_str}: Impossible de lire le fichier log entities {log_file.name} - {e}", exc_info=True)
                current_status["error_reading_log_file"] = f"Could not read log entities file: {log_file.name}"


        audit_log_data: list[Any] = []
        audit_log_file_path = job_dir / "audit_log.json" # Chemin direct
        if await run_in_threadpool(audit_log_file_path.exists):
            try:
                async with aiofiles.open(audit_log_file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                audit_log_data = json.loads(content)
            except Exception as e:
                logger.error(f"Job {job_id_str}: Impossible de lire ou parser audit_log.json - {e}", exc_info=True)
                current_status["error_reading_audit_log"] = "Could not read audit log file."
        
        response_payload = {
            "status": "finished", # Statut principal
            "anonymized_text": anonymized_text,
            "mapping_csv": mapping_csv,
            "log_csv": log_csv,
            "audit_log": audit_log_data,
        }
        # S'il y a eu une erreur au niveau du moteur (enregistrée dans status.json par run_anonymization_job_sync)
        # on la reporte ici aussi.
        if current_status.get("error"):
            response_payload["error"] = current_status.get("error")
        
        # Ajouter les erreurs de lecture de fichiers spécifiques si elles existent
        if "error_reading_output_file" in current_status: response_payload["error_reading_output_file"] = current_status["error_reading_output_file"]
        if "error_reading_mapping_file" in current_status: response_payload["error_reading_mapping_file"] = current_status["error_reading_mapping_file"]
        if "error_reading_log_file" in current_status: response_payload["error_reading_log_file"] = current_status["error_reading_log_file"]
        if "error_reading_audit_log" in current_status: response_payload["error_reading_audit_log"] = current_status["error_reading_audit_log"]

        return JSONResponse(content=response_payload)

    elif current_status["status"] == "error":
        logger.warning(f"Statut du job {job_id_str}: Erreur reportée - {current_status.get('error')}")
        return JSONResponse(content=current_status) # Renvoyer le statut d'erreur complet
    else: # 'pending' ou autre statut intermédiaire
        return JSONResponse(content=current_status)


@app.get("/files/{job_id}/{file_type}")
async def get_file_endpoint(job_id: uuid.UUID, file_type: str, as_attachment: bool = False):
    job_id_str = str(job_id)
    logger.info(f"Demande de fichier '{file_type}' pour le job {job_id_str}, as_attachment={as_attachment}")
    job_dir = JOBS_DIR / job_id_str

    if not await run_in_threadpool(job_dir.exists):
        logger.warning(f"Téléchargement de fichier: Job {job_id_str} non trouvé.")
        raise HTTPException(status_code=404, detail="Job not found")

    patterns = {
        "output": f"{job_id_str}_anonymise_*", # Plus spécifique pour éviter confusion entre jobs
        "mapping": f"{job_id_str}_mapping_*.csv",
        "log": f"{job_id_str}_entities_*.csv",
        "deanonymized": f"{job_id_str}_deanonymise_*.txt", # À ajuster si deanonymize_api est utilisé
        "report": "report.json", # Généralement pour deanonymize_api
        "audit": "audit_log.json" # Pour anonymize
    }

    if file_type not in patterns:
        logger.warning(f"Téléchargement de fichier: Type de fichier invalide '{file_type}' pour job {job_id_str}.")
        raise HTTPException(status_code=400, detail="Invalid file_type")

    pattern = patterns[file_type]
    file_path_to_serve: Optional[Path] = None

    def find_file_sync() -> Optional[Path]:
        # Pour les fichiers spécifiques comme audit_log.json ou report.json
        if file_type in {"audit", "report"}:
            p = job_dir / pattern # Le pattern est déjà le nom de fichier exact
            return p if p.is_file() else None
        else:
            # Pour les fichiers avec timestamp/extension variable
            matches = sorted(
                [p_sync for p_sync in job_dir.glob(pattern) if p_sync.is_file()],
                key=lambda p: p.stat().st_mtime, reverse=True # Le plus récent
            )
            return matches[0] if matches else None

    try:
        file_path_to_serve = await run_in_threadpool(find_file_sync)
    except Exception as e_find: # Erreur pendant la recherche
        logger.error(f"Job {job_id_str}: Erreur lors de la recherche du fichier '{file_type}' ({pattern}): {e_find}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error finding file '{file_type}' for job {job_id_str}")

    if not file_path_to_serve:
        error_detail = f"{file_type.capitalize()} file not found for job {job_id_str} (pattern: {pattern})."
        logger.warning(f"Téléchargement de fichier: {error_detail}")
        raise HTTPException(status_code=404, detail=error_detail)

    logger.info(f"Job {job_id_str}: Service du fichier '{file_path_to_serve.name}' (type: {file_type}).")
    
    # Déterminer le media_type pour FileResponse si as_attachment=True
    media_type = "application/octet-stream" # Par défaut
    if file_type == "mapping" or file_type == "log":
        media_type = "text/csv"
    elif file_type == "output" and file_path_to_serve.suffix == ".txt":
        media_type = "text/plain"
    elif file_type == "output" and file_path_to_serve.suffix == ".json":
        media_type = "application/json"
    # Ajouter d'autres types MIME si nécessaire pour output (docx, xlsx, pdf)
    
    if as_attachment:
        return FileResponse(str(file_path_to_serve), filename=file_path_to_serve.name, media_type=media_type)
    else:
        # Renvoyer le contenu en JSON (comme avant)
        try:
            async with aiofiles.open(file_path_to_serve, "r", encoding="utf-8") as f:
                content_str = await f.read()

            if file_type in {"audit", "report"}: # Ces fichiers sont nativement JSON
                file_content_for_json_response = json.loads(content_str)
            else: # Les autres sont du texte brut (txt, csv)
                file_content_for_json_response = content_str

            return JSONResponse(content={"filename": file_path_to_serve.name, "content": file_content_for_json_response})
        except Exception as e_read_serve: # Erreur de lecture ou de parsing JSON
            logger.error(f"Job {job_id_str}: Erreur lors de la lecture du fichier '{file_path_to_serve.name}' pour la réponse JSON: {e_read_serve}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Could not read or parse file content for {file_path_to_serve.name}")