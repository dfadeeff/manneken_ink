"""Clerk session-token verification.

Networkless verification: the token is checked against Clerk's JWKS (fetched and
cached by PyJWKClient), never by calling Clerk on every request. The parent row
is created on first sight of a Clerk user id.
"""

import base64
import logging
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings, get_settings
from .db import get_db
from .models import Learner, Parent

log = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)

DEV_PARENT_CLERK_ID = "dev_local_parent"


def jwks_url(settings: Settings) -> str | None:
    if settings.clerk_jwks_url:
        return settings.clerk_jwks_url
    # A Clerk publishable key is "pk_<env>_<base64 of 'frontend-api-host$'>".
    parts = settings.clerk_publishable_key.split("_", 2)
    if len(parts) != 3 or not parts[2]:
        return None
    padded = parts[2] + "=" * (-len(parts[2]) % 4)
    try:
        host = base64.b64decode(padded).decode().rstrip("$")
    except Exception:  # noqa: BLE001
        return None
    return f"https://{host}/.well-known/jwks.json"


@lru_cache
def _jwk_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True)


async def _clerk_user_id(token: str, settings: Settings) -> str:
    url = jwks_url(settings)
    if not url:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Clerk is not configured on the server (CLERK_PUBLISHABLE_KEY / CLERK_JWKS_URL)",
        )

    client = _jwk_client(url)
    try:
        # PyJWKClient does blocking HTTP on a cache miss.
        signing_key = await run_in_threadpool(client.get_signing_key_from_jwt, token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"require": ["exp", "sub"], "verify_aud": False},
            leeway=10,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session token") from exc

    # Clerk puts the calling origin in "azp"; reject a token minted for another app.
    azp = claims.get("azp")
    if azp and settings.origins and azp not in settings.origins:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token issued for a different origin")

    return claims["sub"]


async def current_parent(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Parent:
    if settings.dev_auth_bypass:
        clerk_user_id = DEV_PARENT_CLERK_ID
    else:
        if credentials is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue")
        clerk_user_id = await _clerk_user_id(credentials.credentials, settings)

    parent = await db.scalar(select(Parent).where(Parent.clerk_user_id == clerk_user_id))
    if parent is None:
        parent = Parent(clerk_user_id=clerk_user_id)
        db.add(parent)
        await db.commit()
        await db.refresh(parent)
    return parent


async def owned_learner(learner_id: str, parent: Parent, db: AsyncSession) -> Learner:
    """Every learner-scoped query goes through here. This is what makes the old
    shared-global-session bug structurally impossible to reintroduce."""
    learner = await db.scalar(
        select(Learner).where(Learner.id == learner_id, Learner.parent_id == parent.id)
    )
    if learner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Learner not found")
    return learner
