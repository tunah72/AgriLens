"""
Authentication helpers for JWT-protected backend endpoints.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlmodel import Session

from backend.app.config import settings
from backend.app.db import crud, get_session
from backend.app.db.orm_models import User
from backend.app.services.cache import get_cache_service

bearer_scheme = HTTPBearer(auto_error=False)


def is_token_blacklisted(token: str) -> bool:
    """Check if token was revoked via logout."""
    cache = get_cache_service()
    return cache.get(f"jwt_blacklist:{token}") is not None


def blacklist_token(token: str, expire_seconds: int | None = None) -> bool:
    """Revoke a token by adding it to Redis blacklist with TTL."""
    cache = get_cache_service()
    ttl = expire_seconds if expire_seconds is not None else (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return cache.set(f"jwt_blacklist:{token}", "revoked", expire=ttl)

def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_subject(token: str) -> uuid.UUID:
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_error
        return uuid.UUID(subject)
    except (JWTError, ValueError) as exc:
        raise credentials_error from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud.get_user_by_id(session, _decode_subject(credentials.credentials))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User | None:
    if credentials is None:
        return None
    user = crud.get_user_by_id(session, _decode_subject(credentials.credentials))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user
