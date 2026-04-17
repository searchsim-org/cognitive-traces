"""Decode HS256 JWT tokens issued by NextAuth (with our custom encoder)."""

from typing import Any

from jose import JWTError, jwt as jose_jwt


class InvalidTokenError(Exception):
    """Raised when the token cannot be decoded or is otherwise invalid."""


def decode_hs256(token: str, secret: str) -> dict[str, Any]:
    try:
        return jose_jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
