# /home/debian/anonyfiles/anonyfiles_api/deanonymize_api.py

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pathlib import Path
import shutil
import uuid
import json
import logging

from fastapi.responses import JSONResponse

# --- DEBUT BLOC D'IMPORT (normalement déjà corrigé et fonctionnel) ---
try:
    from anonyfiles.anonyfiles_cli.anonymizer.deanonymize import Deanonymizer
    from anonyfiles.anonyfiles_cli.anonymizer.file_utils import default_output, ensure_folder, timestamp
    from anonyfiles.anonyfiles_cli.anonymizer.run_logger import log_run_event
    from anonyfiles.anonyfiles_cli.cli_logger import CLIUsageLogger
except ImportError:
    import sys
    cli_path = Path(__file__).resolve().parent.parent / "anonyfiles_cli"
    if str(cli_path) not in sys.path:
        sys.path.insert(0, str(cli_path)) 
    from anonymizer.deanonymize import Deanonymizer
    from anonymizer.file_utils import default_output, ensure_folder, timestamp
    from anonymizer.run_logger import log_run_event
    from cli_logger import CLIUsageLogger
# --- FIN BLOC D'IMPORT ---

router = APIRouter()
JOBS_DIR = Path("jobs")
JOBS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

def run_deanonymization_job(
    job_id: str,
    input_path: Path,
    mapping_path: Path,
    permissive: bool,
):
    run_dir = input_path.parent
    original_input_name_for_status = input_path.name
    try:
        logger.info(f"[{job_id}] Démarrage de la désanonymisation pour {input_path.name}")
        deanonymizer = Deanonymizer(str(mapping_path), strict=not permissive)

        # Vérifier si le mapping a été chargé correctement (en regardant les map_loading_warnings)
        if deanonymizer.map_loading_warnings and not deanonymizer.code_to_originals:
            warning_message = f"Échec critique du chargement du fichier mapping '{mapping_path}'. Avertissements: {deanonymizer.map_loading_warnings}"
            logger.error(f"[{job_id}] {warning_message}")
            # Mettre à jour le statut du job avec cette erreur spécifique
            status_payload_error = {"status": "error", "error": warning_message, "original_input_name": original_input_name_for_status}
            if run_dir.exists():
                 (run_dir / "status.json").write_text(json.dumps(status_payload_error), encoding="utf-8")
            # Pas besoin de lever une exception ici, la tâche de fond se terminera et le statut reflétera l'erreur.
            return # Arrêter le traitement si le mapping est inutilisable

        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        output_filename = input_path.stem + "_deanonymise_" + timestamp() + input_path.suffix
        output_path = run_dir / output_filename
        
        report_file_path = run_dir / "report.json" # Renommé pour clarté
        status_path = run_dir / "status.json"

        result_text, report_data_from_deanonymizer = deanonymizer.deanonymize_text(content, dry_run=False)

        # --- DÉBUT SECTION CORRIGÉE POUR LA SÉRIALISATION JSON DU RAPPORT ---
        report_data_serializable = dict(report_data_from_deanonymizer) 

        # Convertir les sets en listes pour les champs connus qui en contiennent
        if "map_collisions_details" in report_data_serializable and report_data_serializable["map_collisions_details"]:
            report_data_serializable["map_collisions_details"] = {
                code: list(originals) 
                for code, originals in report_data_serializable["map_collisions_details"].items()
            }
        
        # Les champs comme 'distinct_codes_in_text_list' et 
        # 'codes_from_text_not_found_in_mapping_list' sont déjà des listes
        # dans la dernière version de Deanonymizer.
        # 'warnings_generated_during_deanonymization' est aussi une liste de strings.
        # --- FIN SECTION CORRIGÉE POUR LA SÉRIALISATION JSON DU RAPPORT ---

        output_path.write_text(result_text, encoding="utf-8")
        report_file_path.write_text(json.dumps(report_data_serializable, indent=2, ensure_ascii=False), encoding="utf-8")
        
        status_payload = {"status": "finished", "error": None, "original_input_name": original_input_name_for_status}
        status_path.write_text(json.dumps(status_payload), encoding="utf-8")

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
        status_payload_error = {"status": "error", "error": error_msg, "original_input_name": original_input_name_for_status}
        if run_dir is not None and run_dir.exists():
             (run_dir / "status.json").write_text(json.dumps(status_payload_error), encoding="utf-8")
        else:
            logger.error(f"[{job_id}] Le répertoire du job {run_dir} n'existe pas, impossible d'écrire le statut d'erreur.")

        log_run_event(
            logger=CLIUsageLogger,
            run_id=job_id,
            input_file=str(input_path) if input_path and input_path.exists() else "Non défini/Non trouvé", 
            output_file="",
            mapping_file=str(mapping_path) if mapping_path and mapping_path.exists() else "Non défini/Non trouvé",
            log_entities_file="",
            entities_detected=[],
            total_replacements=0,
            audit_log=[f"Erreur système: {error_msg}"], # Loguer l'erreur système dans audit_log
            status="error",
            error=error_msg
        )

@router.post("/api/deanonymize/")
async def deanonymize_file_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mapping: UploadFile = File(...),
    permissive: bool = Form(False)
):
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    ensure_folder(job_dir) 

    input_filename = file.filename if file.filename else "input_file_to_deanonymize"
    mapping_filename = mapping.filename if mapping.filename else "mapping_file.csv"
    
    input_path = job_dir / input_filename
    mapping_path = job_dir / mapping_filename

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Job {job_id}: Fichier d'entrée '{input_filename}' sauvegardé dans '{input_path}'")
    except Exception as e_save_input:
        logger.error(f"Job {job_id}: Échec de la sauvegarde du fichier d'entrée '{input_filename}': {e_save_input}", exc_info=True)
        (job_dir / "status.json").write_text(json.dumps({"status": "error", "error": f"Could not save input file: {input_filename}", "original_input_name": input_filename}), encoding="utf-8")
        await file.close()
        raise HTTPException(status_code=500, detail=f"Could not save input file: {input_filename}")
    finally:
        await file.close()

    try:
        with open(mapping_path, "wb") as buffer:
            shutil.copyfileobj(mapping.file, buffer)
        logger.info(f"Job {job_id}: Fichier de mapping '{mapping_filename}' sauvegardé dans '{mapping_path}'")
    except Exception as e_save_mapping:
        logger.error(f"Job {job_id}: Échec de la sauvegarde du fichier de mapping '{mapping_filename}': {e_save_mapping}", exc_info=True)
        (job_dir / "status.json").write_text(json.dumps({"status": "error", "error": f"Could not save mapping file: {mapping_filename}", "original_input_name": input_filename}), encoding="utf-8")
        await mapping.close()
        raise HTTPException(status_code=500, detail=f"Could not save mapping file: {mapping_filename}")
    finally:
        await mapping.close()

    status_init_payload = {"status": "pending", "error": None, "original_input_name": input_filename}
    (job_dir / "status.json").write_text(json.dumps(status_init_payload), encoding="utf-8")

    background_tasks.add_task(
        run_deanonymization_job,
        job_id=job_id,
        input_path=input_path,
        mapping_path=mapping_path,
        permissive=permissive,
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/api/deanonymize_status/{job_id}")
async def get_deanonymize_status(job_id: str):
    job_dir = JOBS_DIR / job_id
    status_file = job_dir / "status.json"
    if not status_file.is_file():
        logger.warning(f"Job {job_id}: Fichier status.json non trouvé ou n'est pas un fichier.")
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or status file missing/invalid.")

    try:
        with open(status_file, "r", encoding="utf-8") as f:
            status_data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Job {job_id}: Impossible de parser status.json.", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not parse status file for job {job_id}.")


    if status_data.get("status") == "finished":
        try:
            original_input_name = status_data.get("original_input_name", "input_unknown_suffix")
            original_suffix = Path(original_input_name).suffix if original_input_name else ".txt"

            output_files = sorted(
                job_dir.glob(f"*_deanonymise_*{original_suffix}"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            output_file_path = output_files[0] if output_files else None
            
            report_file_path = job_dir / "report.json"

            deanonymized_text_content = ""
            if output_file_path and output_file_path.exists():
                deanonymized_text_content = output_file_path.read_text(encoding="utf-8")
            
            report_content_from_file = {} # Renommé pour éviter confusion avec report_data_serializable
            if report_file_path.exists():
                report_content_from_file = json.loads(report_file_path.read_text(encoding="utf-8"))
            
            return {
                "status": "finished",
                "deanonymized_text": deanonymized_text_content,
                "report": report_content_from_file, # Le rapport complet (maintenant sérialisable)
                # 'audit_log' dans la réponse API pointe vers les avertissements du rapport
                "audit_log": report_content_from_file.get("warnings_generated_during_deanonymization", []),
                 "error": status_data.get("error") 
            }
        except Exception as e:
            logger.error(f"Erreur récupération fichiers pour job terminé {job_id}: {str(e)}", exc_info=True)
            status_data["error"] = f"Job finished but could not retrieve/process result files: {str(e)}"
            status_data["status"] = "error" 
            return status_data
    else: 
        return status_data