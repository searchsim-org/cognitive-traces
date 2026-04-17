import time

import pytest
from jose import jwt as jose_jwt

from app.auth.jwt import InvalidTokenError, decode_hs256

SECRET = "test-secret-32bytes-min-xxxxxxxx"


def _sign(claims: dict) -> str:
    return jose_jwt.encode(claims, SECRET, algorithm="HS256")


def test_decodes_valid_hs256_token():
    claims = {"sub": "1", "github_id": 42, "github_login": "ada", "exp": int(time.time()) + 60}
    token = _sign(claims)
    out = decode_hs256(token, SECRET)
    assert out["github_id"] == 42
    assert out["github_login"] == "ada"


def test_rejects_expired_token():
    claims = {"sub": "1", "github_id": 1, "exp": int(time.time()) - 10}
    token = _sign(claims)
    with pytest.raises(InvalidTokenError):
        decode_hs256(token, SECRET)


def test_rejects_wrong_secret():
    claims = {"sub": "1", "github_id": 1, "exp": int(time.time()) + 60}
    token = jose_jwt.encode(claims, "different-secret", algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        decode_hs256(token, SECRET)


def test_rejects_garbage():
    with pytest.raises(InvalidTokenError):
        decode_hs256("not.a.jwt", SECRET)
