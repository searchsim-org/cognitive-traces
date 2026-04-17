"""User repository — upsert from JWT claims."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


def upsert_by_github_id(db: Session, claims: dict) -> User:
    """Find a user by github_id (canonical); create if missing, update mutable fields if present."""
    gid = int(claims["github_id"])
    user = db.scalar(select(User).where(User.github_id == gid))
    if user is None:
        user = User(
            github_id=gid,
            github_login=claims["github_login"],
            name=claims.get("name"),
            email=claims.get("email"),
            avatar_url=claims.get("avatar_url"),
        )
        db.add(user)
        db.flush()  # populate id without committing
        return user

    user.github_login = claims["github_login"]
    if claims.get("name") is not None:
        user.name = claims["name"]
    if claims.get("email") is not None:
        user.email = claims["email"]
    if claims.get("avatar_url") is not None:
        user.avatar_url = claims["avatar_url"]
    db.flush()
    return user
