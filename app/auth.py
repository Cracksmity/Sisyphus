import os
import secrets
from fastapi import Header, HTTPException


def _expected_api_token() -> str:
    token = os.getenv("SYSIPHUS_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="SYSIPHUS_API_TOKEN no configurado.")
    return token


def require_api_token(authorization: str | None = Header(default=None)) -> None:
    """
    Valida el token de API enviado como 'Authorization: Bearer <token>'.
    Usa secrets.compare_digest para evitar timing attacks.
    """
    expected = _expected_api_token()
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Token de API inválido.")


def get_current_user_id(x_user_id: str | None = Header(default=None)) -> str:
    if not x_user_id or len(x_user_id.strip()) < 3:
        raise HTTPException(status_code=401, detail="Usuario no autenticado.")
    return x_user_id.strip()[:128]
