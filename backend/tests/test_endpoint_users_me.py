from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


def _override_db_factory(db_session):
    def _override():
        yield db_session
    return _override


def test_me_401_without_token(db_session):
    app.dependency_overrides[get_db] = _override_db_factory(db_session)
    try:
        r = TestClient(app).get("/api/v1/users/me")
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_me_returns_upserted_user(db_session, make_token):
    app.dependency_overrides[get_db] = _override_db_factory(db_session)
    try:
        token = make_token(github_id=7, github_login="alan")
        r = TestClient(app).get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["github_id"] == 7
        assert body["github_login"] == "alan"
    finally:
        app.dependency_overrides.clear()
