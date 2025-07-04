# anonyfiles/anonyfiles_api/routers/jobs.py

from fastapi import APIRouter, HTTPException, status, Response
from fastapi.concurrency import run_in_threadpool # Ajouté
import aiofiles.os as aio_os
import uuid
# import logging # Logger est maintenant importé depuis core_config

from ..job_utils import Job
# Importer depuis le nouveau module de configuration central
from ..core_config import logger, set_job_id # Importer logger et context

router = APIRouter()
# 'logger' est maintenant importé de core_config et utilisé directement

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tâches"])
async def delete_job_endpoint(job_id: uuid.UUID): # job_id peut être str aussi
    """Delete all files related to a job.

    Args:
        job_id: Identifier of the job directory to remove.

    Returns:
        An empty ``204 NO CONTENT`` response when successful.
    """
    job_id_str = str(job_id)
    set_job_id(job_id_str)
    current_job = Job(job_id_str)
    logger.info(f"Requête de suppression pour l'ID de tâche: {job_id_str}")

    if not await aio_os.path.exists(current_job.job_dir):
        logger.warning(f"Tâche {job_id_str} non trouvée pour suppression. Répertoire: {current_job.job_dir}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche non trouvée")

    deleted_successfully = await current_job.delete_job_directory_async()

    if not deleted_successfully:
        if await aio_os.path.exists(current_job.job_dir):
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Impossible de supprimer le répertoire de la tâche")
        else:
            logger.info(f"Tâche {job_id_str}: Répertoire non trouvé après tentative de suppression ou déjà supprimé. Opération considérée comme réussie.")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
