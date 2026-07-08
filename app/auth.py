import os
from fastapi import Header, HTTPException


def _expected_api_token() -> str:
    token = os.getenv("SYSIPHUS_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="SYSIPHUS_API_TOKEN no configurado.")
    return token


def require_api_token(x_api_token: str | None = Header(default=None)) -> None:
    expected = _expected_api_token()
    if x_api_token != expected:
        raise HTTPException(status_code=401, detail="Token de API inválido.")


def get_current_user_id(x_user_id: str | None = Header(default=None)) -> str:
    if not x_user_id or len(x_user_id.strip()) < 3:
        raise HTTPException(status_code=401, detail="Usuario no autenticado.")
    return x_user_id.strip()[:128]
