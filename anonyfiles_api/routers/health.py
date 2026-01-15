from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health() -> dict:
    """Simple health-check endpoint.

    Returns:
        ``{"status": "ok"}`` if the service is running.
    """
    return {"status": "ok"}
