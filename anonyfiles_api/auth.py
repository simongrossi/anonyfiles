"""Optional API-key authentication for public API deployments."""

from __future__ import annotations

import os
from hmac import compare_digest
from typing import Iterable

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from starlette.websockets import WebSocket

API_KEY_HEADER_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)


def _configured_api_key(request_or_websocket: Request | WebSocket) -> str:
    settings = getattr(request_or_websocket.app.state, "settings", None)
    if settings is None:
        return os.environ.get("ANONYFILES_API_KEY", "").strip()
    return str(getattr(settings, "api_key", "") or "").strip()


def _bearer_token(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def _has_valid_api_key(expected_key: str, candidates: Iterable[str | None]) -> bool:
    if not expected_key:
        return True
    return any(
        compare_digest(expected_key, candidate.strip())
        for candidate in candidates
        if candidate and candidate.strip()
    )


async def require_api_key(
    request: Request,
    header_key: str | None = Security(api_key_header),
    bearer_credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth),
) -> None:
    """FastAPI dependency enforcing API-key auth only when configured."""
    expected_key = _configured_api_key(request)
    bearer_token = bearer_credentials.credentials if bearer_credentials else None

    if _has_valid_api_key(expected_key, (header_key, bearer_token)):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Clé API manquante ou invalide.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def websocket_has_valid_api_key(websocket: WebSocket) -> bool:
    """Validate WebSocket auth using headers or query params when auth is active."""
    expected_key = _configured_api_key(websocket)
    authorization = websocket.headers.get("authorization")
    return _has_valid_api_key(
        expected_key,
        (
            websocket.headers.get(API_KEY_HEADER_NAME),
            _bearer_token(authorization),
            websocket.query_params.get("api_key"),
            websocket.query_params.get("token"),
        ),
    )
