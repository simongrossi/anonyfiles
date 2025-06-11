# anonyfiles/anonyfiles_api/routers/files.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
import uuid
import json
# import logging # Logger est maintenant importé depuis core_config
from typing import Optional 

from ..job_utils import Job
# Importer depuis le nouveau module de configuration central
from ..core_config import logger, set_job_id # Importer logger et set_job_id

router = APIRouter()
# 'logger' est maintenant importé de core_config et utilisé directement

@router.get("/files/{job_id}/{file_key}", tags=["Fichiers"])
async def get_file_endpoint(job_id: uuid.UUID, file_key: str, as_attachment: bool = False):
    """Serve a result file for a given job.

    Args:
        job_id: Identifier of the job directory.
        file_key: Type of file to retrieve (output, mapping, log_entities, audit_log).
        as_attachment: If ``True``, force download rather than inline display.

    Returns:
        A :class:`FileResponse` with the requested file.
    """
    job_id_str = str(job_id)
    set_job_id(job_id_str)
    current_job = Job(job_id_str)
    logger.info(f"Demande fichier clé '{file_key}' pour tâche {job_id_str}, en pièce jointe={as_attachment}")

    if not await current_job.check_exists_async(check_status_file=False):
        logger.warning(f"Téléchargement: Tâche {job_id_str} non trouvée (répertoire).")
        raise HTTPException(status_code=404, detail="Répertoire de la tâche non trouvé")

    valid_file_keys = {"output", "mapping", "log_entities", "audit_log"}
    if file_key not in valid_file_keys:
        logger.warning(f"Téléchargement: Clé de fichier invalide '{file_key}' pour tâche {job_id_str}.")
        raise HTTPException(status_code=400, detail=f"Clé de fichier invalide. Valides: {', '.join(valid_file_keys)}")

    file_path_to_serve: Optional[Path] = None
    try:
        file_path_to_serve = await run_in_threadpool(current_job.get_file_path_sync, file_key)
    except Exception as e_find:
        logger.error(f"Tâche {job_id_str}: Erreur de recherche du fichier clé '{file_key}': {e_find}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche du fichier pour la clé '{file_key}'.")

    if not file_path_to_serve or not await run_in_threadpool(file_path_to_serve.is_file):
        error_detail = f"Fichier {file_key.capitalize()} non trouvé pour la tâche {job_id_str}."
        logger.warning(f"Téléchargement: {error_detail} (Chemin: {file_path_to_serve})")
        raise HTTPException(status_code=404, detail=error_detail)

    logger.info(f"Tâche {job_id_str}: Service du fichier '{file_path_to_serve.name}' (clé: {file_key}).")

    media_type = "application/octet-stream"
    file_suffix = file_path_to_serve.suffix.lower()

    if file_key in ["mapping", "log_entities"] and file_suffix == ".csv": media_type = "text/csv"
    elif file_key == "output":
        if file_suffix == ".txt": media_type = "text/plain"
        # ... (autres types media)
        elif file_suffix == ".json": media_type = "application/json"
        elif file_suffix == ".csv": media_type = "text/csv"
        elif file_suffix == ".docx": media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_suffix == ".xlsx": media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif file_suffix == ".pdf": media_type = "application/pdf"
    elif file_key == "audit_log" and file_path_to_serve.name == "audit_log.json": media_type = "application/json"


    if as_attachment:
        return FileResponse(str(file_path_to_serve), filename=file_path_to_serve.name, media_type=media_type)
    else:
        return FileResponse(str(file_path_to_serve), media_type=media_type)
