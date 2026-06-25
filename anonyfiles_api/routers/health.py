from fastapi import APIRouter, Request

from anonyfiles_core.anonymizer.spacy_status import get_spacy_status

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health(request: Request) -> dict:
    """Simple health-check endpoint.

    Returns:
        ``{"status": "ok"}`` if the service is running, with spaCy diagnostics.
    """
    return {
        "status": "ok",
        "spacy": _spacy_status_from_app_state(request),
    }


@router.get("/health/spacy", tags=["Health"])
async def spacy_health(request: Request) -> dict:
    """Detailed spaCy/model diagnostic endpoint."""
    return _spacy_status_from_app_state(request)


def _spacy_status_from_app_state(request: Request) -> dict:
    base_config = getattr(request.app.state, "BASE_CONFIG", None) or {}
    model_name = base_config.get("spacy_model", "fr_core_news_md")
    return get_spacy_status(model_name)
