# backend/tests/test_auth_deps.py
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.auth.deps import get_current_user, get_current_user_optional
from app.db.session import get_db


@pytest.fixture()
def app(db_session):
    app = FastAPI()

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db

    @app.get("/required")
    def required(user=Depends(get_current_user)):
        return {"github_id": user.github_id, "login": user.github_login}

    @app.get("/optional")
    def optional(user=Depends(get_current_user_optional)):
        return {"login": user.github_login if user else None}

    return app


def test_required_401_without_token(app):
    r = TestClient(app).get("/required")
    assert r.status_code == 401


def test_required_returns_user_with_valid_token(app, make_token):
    token = make_token(github_id=99, github_login="grace")
    r = TestClient(app).get("/required", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == {"github_id": 99, "login": "grace"}


def test_required_401_with_garbage_token(app):
    r = TestClient(app).get("/required", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


def test_optional_returns_none_without_token(app):
    r = TestClient(app).get("/optional")
    assert r.status_code == 200
    assert r.json() == {"login": None}


def test_optional_swallows_bad_token(app):
    r = TestClient(app).get("/optional", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 200
    assert r.json() == {"login": None}
