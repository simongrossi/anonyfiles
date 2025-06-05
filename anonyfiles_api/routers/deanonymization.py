# anonyfiles/anonyfiles_api/routers/deanonymization.py

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Request # Ajout de Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
import aiofiles
import uuid
import json
import sys
from typing import Optional, Dict, Any # Ajouté pour la cohérence du typage

# Importer Job depuis job_utils (JOBS_DIR est géré à l'intérieur de Job ou core_config)
from ..job_utils import Job

# MODIFICATION ICI: Importer SEULEMENT logger depuis core_config.
# BASE_CONFIG n'est plus défini globalement dans core_config.py.
# Si la logique de désanonymisation avait besoin de BASE_CONFIG, il faudrait le passer en argument
# aux fonctions concernées, récupéré depuis request.app.state.BASE_CONFIG dans l'endpoint.
# Pour l'instant, nous supposons que la désanonymisation n'a pas besoin de BASE_CONFIG.
from ..core_config import logger

from anonyfiles_cli.anonymizer.deanonymize import Deanonymizer
from anonyfiles_cli.anonymizer.file_utils import (
    ensure_folder,
    timestamp,
)
from anonyfiles_cli.anonymizer.run_logger import log_run_event
from anonyfiles_cli.cli_logger import CLIUsageLogger  # Utilisé pour log_run_event

router = APIRouter()
# 'logger' est maintenant importé depuis core_config

def run_deanonymization_job_sync(
    job_id: str,
    input_path: Path,
    mapping_path: Path,
    permissive: bool,
    # Si BASE_CONFIG était nécessaire, il faudrait l'ajouter ici :
    # passed_base_config: Optional[Dict[str, Any]] = None
):
    current_job = Job(job_id)
    run_dir = current_job.job_dir
    original_input_name_for_status = input_path.name # Pour le fichier status.json

    # Si BASE_CONFIG était passé et nécessaire:
    # if passed_base_config is None or not passed_base_config:
    #     logger.error(f"Tâche {job_id} (désanonymisation): La configuration de base n'a pas été fournie.")
    #     current_job.set_status_as_error_sync("Configuration de base manquante pour la désanonymisation.")
    #     return

    try:
        logger.info(f"[{job_id}] Démarrage de la désanonymisation pour {input_path.name}")
        deanonymizer = Deanonymizer(str(mapping_path), strict=not permissive)

        if deanonymizer.map_loading_warnings and not deanonymizer.code_to_originals:
            warning_message = f"Échec critique du chargement du fichier mapping '{mapping_path}'. Avertissements: {deanonymizer.map_loading_warnings}"
            logger.error(f"[{job_id}] {warning_message}")
            # Mettre original_input_name dans le statut d'erreur
            error_payload_for_status = {"status": "error", "error": warning_message, "original_input_name": original_input_name_for_status}
            with open(current_job.status_file_path, "w", encoding="utf-8") as f_status:
                 json.dump(error_payload_for_status, f_status)
            return

        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        output_filename = input_path.stem + "_deanonymise_" + timestamp() + input_path.suffix
        output_path = run_dir / output_filename
        report_file_path = run_dir / "report.json"

        result_text, report_data_from_deanonymizer = deanonymizer.deanonymize_text(content, dry_run=False)
        
        report_data_serializable = dict(report_data_from_deanonymizer)
        if "map_collisions_details" in report_data_serializable and report_data_serializable["map_collisions_details"]:
            report_data_serializable["map_collisions_details"] = {
                code: list(originals) 
                for code, originals in report_data_serializable["map_collisions_details"].items()
            }

        output_path.write_text(result_text, encoding="utf-8")
        report_file_path.write_text(json.dumps(report_data_serializable, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # Payload pour set_status_as_finished_sync, incluant original_input_name
        # et le journal d'audit (qui sont les warnings pour la désanonymisation)
        engine_like_result_for_status = {
            "audit_log": report_data_serializable.get("warnings_generated_during_deanonymization", []),
            "original_input_name": original_input_name_for_status # Ajouté pour la cohérence du statut
        }
        # Le statut doit inclure original_input_name pour être récupéré correctement par get_deanonymize_status
        # La méthode set_status_as_finished_sync de Job a été conçue pour Anonymize,
        # nous allons directement écrire le fichier status.json ici pour plus de contrôle.
        status_payload_finished = {"status": "finished", "error": None, "original_input_name": original_input_name_for_status}
        with open(current_job.status_file_path, "w", encoding="utf-8") as f_status:
            json.dump(status_payload_finished, f_status)
        # Sauvegarder le journal d'audit séparément (si la classe Job ne le fait pas pour deanonymize)
        with open(current_job.audit_log_file_path, "w", encoding="utf-8") as f_audit:
            json.dump(engine_like_result_for_status["audit_log"], f_audit)


        log_run_event(
            logger=CLIUsageLogger,
            run_id=job_id,
            input_file=str(input_path),
            output_file=str(output_path),
            mapping_file=str(mapping_path),
            log_entities_file="", 
            entities_detected=report_data_serializable.get("distinct_codes_in_text_list", []),
            total_replacements=report_data_serializable.get("replacements_successful_count", 0),
            audit_log=report_data_serializable.get("warnings_generated_during_deanonymization", []),
            status="success",
            error=None
        )
        logger.info(f"[{job_id}] Désanonymisation terminée avec succès pour {input_path.name}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] Erreur de désanonymisation pour {input_path.name} : {error_msg}", exc_info=True)
        # Mettre à jour le statut avec original_input_name
        error_payload_for_status = {"status": "error", "error": error_msg, "original_input_name": original_input_name_for_status}
        # S'assurer que le répertoire existe avant d'écrire le statut
        current_job.job_dir.mkdir(parents=True, exist_ok=True)
        with open(current_job.status_file_path, "w", encoding="utf-8") as f_status:
             json.dump(error_payload_for_status, f_status)

        log_run_event(
            logger=CLIUsageLogger,
            run_id=job_id,
            input_file=str(input_path) if input_path and input_path.exists() else "Non défini/Non trouvé", 
            output_file="",
            mapping_file=str(mapping_path) if mapping_path and mapping_path.exists() else "Non défini/Non trouvé",
            log_entities_file="",
            entities_detected=[],
            total_replacements=0,
            audit_log=[f"Erreur système: {error_msg}"],
            status="error",
            error=error_msg
        )

@router.post("/deanonymize/", tags=["Désanonymisation"])
async def deanonymize_file_endpoint(
    request: Request, # Ajouté pour potentiellement accéder à app.state si BASE_CONFIG devenait nécessaire
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mapping: UploadFile = File(...),
    permissive: bool = Form(False)
):
    job_id = str(uuid.uuid4())
    current_job = Job(job_id)
    job_dir = current_job.job_dir

    await run_in_threadpool(job_dir.mkdir, parents=True, exist_ok=True)

    input_filename = Path(file.filename).name if file.filename else "input_file_to_deanonymize"
    mapping_filename = Path(mapping.filename).name if mapping.filename else "mapping_file.csv"

    input_path = job_dir / input_filename
    mapping_path = job_dir / mapping_filename

    try:
        async with aiofiles.open(input_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        logger.info(f"Tâche {job_id}: Fichier d'entrée '{input_filename}' sauvegardé dans '{input_path}'")
    except Exception as e_save_input:
        logger.error(f"Tâche {job_id}: Échec de la sauvegarde du fichier d'entrée '{input_filename}': {e_save_input}", exc_info=True)
        # Écrire le statut d'erreur en incluant original_input_name
        error_payload = {"status": "error", "error": f"Impossible de sauvegarder le fichier d'entrée: {input_filename}", "original_input_name": input_filename}
        with open(current_job.status_file_path, "w", encoding="utf-8") as f_status: # Assurer que job_dir existe
            json.dump(error_payload, f_status)
        raise HTTPException(status_code=500, detail=f"Impossible de sauvegarder le fichier d'entrée: {input_filename}")
    finally:
        await file.close()

    try:
        async with aiofiles.open(mapping_path, "wb") as buffer:
            content = await mapping.read()
            await buffer.write(content)
        logger.info(f"Tâche {job_id}: Fichier de mapping '{mapping_filename}' sauvegardé dans '{mapping_path}'")
    except Exception as e_save_mapping:
        logger.error(f"Tâche {job_id}: Échec de la sauvegarde du fichier de mapping '{mapping_filename}': {e_save_mapping}", exc_info=True)
        error_payload = {"status": "error", "error": f"Impossible de sauvegarder le fichier de mapping: {mapping_filename}", "original_input_name": input_filename} # Utiliser input_filename ici aussi
        with open(current_job.status_file_path, "w", encoding="utf-8") as f_status:
            json.dump(error_payload, f_status)
        raise HTTPException(status_code=500, detail=f"Impossible de sauvegarder le fichier de mapping: {mapping_filename}")
    finally:
        await mapping.close()
    
    # Écrire le statut initial en incluant original_input_name
    initial_status_payload = {"status": "pending", "error": None, "original_input_name": input_filename}
    with open(current_job.status_file_path, "w", encoding="utf-8") as f_status:
        json.dump(initial_status_payload, f_status)

    # Si BASE_CONFIG était nécessaire pour run_deanonymization_job_sync:
    # passed_base_config_value = getattr(request.app.state, 'BASE_CONFIG', {})
    # if not passed_base_config_value: # Vérifier si vide ou None
    #     logger.error(f"Tâche {job_id}: BASE_CONFIG est vide ou non chargé, impossible de lancer la désanonymisation.")
    #     # Gérer l'erreur...
    #     raise HTTPException(status_code=500, detail="Configuration de base du serveur manquante.")

    background_tasks.add_task(
        run_deanonymization_job_sync,
        job_id=job_id,
        input_path=input_path,
        mapping_path=mapping_path,
        permissive=permissive,
        # passed_base_config=passed_base_config_value.copy() # Si BASE_CONFIG était nécessaire
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/deanonymize_status/{job_id}", tags=["Désanonymisation"])
async def get_deanonymize_status(job_id: str):
    current_job = Job(job_id)

    if not await current_job.check_exists_async(check_status_file=True):
        logger.warning(f"Tâche {job_id}: status.json non trouvé ou répertoire de tâche inexistant.")
        raise HTTPException(status_code=404, detail=f"Tâche {job_id} non trouvée ou fichier de statut manquant/invalide.")

    status_data = await current_job.get_status_async()
    if status_data is None:
        raise HTTPException(status_code=500, detail=f"Impossible de lire ou parser le fichier de statut pour la tâche {job_id}.")

    if status_data.get("status") == "finished":
        try:
            original_input_name = status_data.get("original_input_name", "input_unknown_suffix")
            original_suffix = Path(original_input_name).suffix if original_input_name and Path(original_input_name).name == original_input_name else ".txt"
            
            output_file_path = await run_in_threadpool(current_job._find_latest_file_sync, f"_deanonymise_*{original_suffix}")
            report_file_path = current_job.job_dir / "report.json"
            # Le journal d'audit pour la désanonymisation est stocké dans audit_log.json par la classe Job,
            # mais run_deanonymization_job_sync l'écrit aussi dans report.json (sous warnings...).
            # Pour être cohérent, on pourrait lire audit_log.json ou extraire des warnings du rapport.
            # Pour l'instant, on prend les warnings du rapport comme audit_log pour ce endpoint.

            deanonymized_text_content = ""
            if output_file_path and await run_in_threadpool(output_file_path.exists):
                async with aiofiles.open(output_file_path, "r", encoding="utf-8") as f:
                    deanonymized_text_content = await f.read()
            
            report_content_from_file = {}
            if await run_in_threadpool(report_file_path.exists):
                async with aiofiles.open(report_file_path, "r", encoding="utf-8") as f:
                    report_content_str = await f.read()
                report_content_from_file = json.loads(report_content_str)
            
            return {
                "status": "finished",
                "deanonymized_text": deanonymized_text_content,
                "report": report_content_from_file, 
                "audit_log": report_content_from_file.get("warnings_generated_during_deanonymization", []),
                "error": status_data.get("error") # Peut y avoir une erreur même si statut "finished" (rare)
            }
        except Exception as e:
            logger.error(f"Erreur de récupération des fichiers pour la tâche de désanonymisation terminée {job_id}: {str(e)}", exc_info=True)
            # Retourner le statut d'erreur si la récupération des fichiers échoue
            error_payload = {"status": "error", 
                             "error": f"Tâche terminée mais impossible de récupérer/traiter les fichiers de résultats: {str(e)}",
                             "original_input_name": status_data.get("original_input_name", "unknown")}
            return JSONResponse(content=error_payload, status_code=500)
    else: 
        return JSONResponse(content=status_data)