"""FastAPI dependencies for resolving the current user from a NextAuth JWT."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import InvalidTokenError, decode_hs256
from app.core.config import settings
from app.db.models import User
from app.db.repositories.users import upsert_by_github_id
from app.db.session import get_db


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        return None
    return parts[1]


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer(authorization)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        claims = decode_hs256(token, settings.NEXTAUTH_SECRET)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    user = upsert_by_github_id(db, claims)
    db.commit()
    return user


def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    token = _extract_bearer(authorization)
    if token is None:
        return None
    try:
        claims = decode_hs256(token, settings.NEXTAUTH_SECRET)
    except InvalidTokenError:
        return None
    user = upsert_by_github_id(db, claims)
    db.commit()
    return user
