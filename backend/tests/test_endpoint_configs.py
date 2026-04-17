from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


def _override_db_factory(db_session):
    def _override():
        yield db_session
    return _override


def test_create_strips_api_keys_before_persisting(db_session, make_token):
    app.dependency_overrides[get_db] = _override_db_factory(db_session)
    try:
        token = make_token(github_id=1, github_login="u")
        payload = {
            "name": "default",
            "config_json": {
                "anthropic_api_key": "sk-must-not-store",
                "analyst_model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "custom_endpoints": [{"id": "e", "name": "x", "api_key": "leak"}],
            },
        }
        r = TestClient(app).post("/api/v1/configs", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 201
        body = r.json()
        assert "anthropic_api_key" not in body["config_json"]
        assert body["config_json"]["analyst_model"] == "claude-3-5-sonnet-20241022"
        assert "api_key" not in body["config_json"]["custom_endpoints"][0]
    finally:
        app.dependency_overrides.clear()


def test_duplicate_name_returns_409(db_session, make_token):
    app.dependency_overrides[get_db] = _override_db_factory(db_session)
    try:
        token = make_token(github_id=1, github_login="u")
        h = {"Authorization": f"Bearer {token}"}
        c = TestClient(app)
        assert c.post("/api/v1/configs", json={"name": "n", "config_json": {}}, headers=h).status_code == 201
        assert c.post("/api/v1/configs", json={"name": "n", "config_json": {}}, headers=h).status_code == 409
    finally:
        app.dependency_overrides.clear()
