from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from backend.config import get_settings


@dataclass
class CurrentUser:
    id: str
    email: str | None = None


_jwk_cache: PyJWKClient | None = None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_cache
    settings = get_settings()
    if _jwk_cache is None:
        _jwk_cache = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")
    return _jwk_cache


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    token = authorization.split(" ", 1)[1]
    try:
        signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    return CurrentUser(id=user_id, email=payload.get("email"))
