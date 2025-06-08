# anonyfiles/anonyfiles_api/routers/websocket_status.py

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..job_utils import Job
from ..core_config import logger

router = APIRouter()

@router.websocket("/ws/{job_id}")
async def websocket_job_status(websocket: WebSocket, job_id: str) -> None:
    """Envoie en temps réel le statut d'un job via WebSocket."""
    await websocket.accept()
    job = Job(job_id)
    if not await job.check_exists_async():
        await websocket.close(code=1008)
        return

    last_payload = None
    try:
        while True:
            status_payload = await job.get_status_async()
            if status_payload is None:
                status_payload = {"status": "error", "error": "status not found"}
                await websocket.send_json(status_payload)
                break
            if status_payload != last_payload:
                await websocket.send_json(status_payload)
                last_payload = status_payload
            if status_payload.get("status") in {"finished", "error"}:
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info(f"Client WebSocket déconnecté pour la tâche {job_id}")
    finally:
        await websocket.close()
