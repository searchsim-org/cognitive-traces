import os
import time

import pytest
from jose import jwt as jose_jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

pytest_plugins = ["pytest_postgresql"]


@pytest.fixture(scope="session")
def postgresql_proc_url(postgresql_proc):
    return (
        f"postgresql://{postgresql_proc.user}@{postgresql_proc.host}:{postgresql_proc.port}/"
        f"{postgresql_proc.dbname}"
    )


@pytest.fixture()
def db_engine(postgresql):
    url = (
        f"postgresql://{postgresql.info.user}@{postgresql.info.host}:{postgresql.info.port}/"
        f"{postgresql.info.dbname}"
    )
    eng = create_engine(url, future=True)
    with eng.begin() as conn:
        conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    s = Session()
    try:
        yield s
    finally:
        s.close()


TEST_SECRET = "test-secret-32bytes-min-xxxxxxxx"


@pytest.fixture()
def auth_secret(monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", TEST_SECRET)
    from app.core.config import settings
    monkeypatch.setattr(settings, "NEXTAUTH_SECRET", TEST_SECRET)
    return TEST_SECRET


@pytest.fixture()
def make_token(auth_secret):
    def _make(github_id: int = 42, github_login: str = "ada", **extra):
        claims = {
            "sub": str(github_id),
            "github_id": github_id,
            "github_login": github_login,
            "name": extra.get("name", "Ada Lovelace"),
            "email": extra.get("email", "ada@example.com"),
            "avatar_url": extra.get("avatar_url"),
            "exp": int(time.time()) + 600,
        }
        return jose_jwt.encode(claims, auth_secret, algorithm="HS256")
    return _make
