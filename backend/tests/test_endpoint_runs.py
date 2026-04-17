from fastapi.testclient import TestClient

from app.db.repositories import runs as runs_repo
from app.db.repositories.users import upsert_by_github_id
from app.db.session import get_db
from app.main import app


def _override_db_factory(db_session):
    def _override():
        yield db_session
    return _override


def _seed(db_session, github_id):
    u = upsert_by_github_id(db_session, {"github_id": github_id, "github_login": f"u{github_id}", "name": None, "email": None, "avatar_url": None})
    runs_repo.create(db_session, user_id=u.id, job_id=f"j-{github_id}", dataset_id="d", dataset_filename="f.csv", total_sessions=3, llm_config_snapshot={"x": 1})
    db_session.commit()
    return u


def test_list_returns_only_own_runs(db_session, make_token):
    _seed(db_session, 1)
    _seed(db_session, 2)

    app.dependency_overrides[get_db] = _override_db_factory(db_session)
    try:
        token = make_token(github_id=1, github_login="u1")
        r = TestClient(app).get("/api/v1/runs", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["job_id"] == "j-1"
    finally:
        app.dependency_overrides.clear()


def test_get_other_users_run_is_404(db_session, make_token):
    _seed(db_session, 1)
    _seed(db_session, 2)
    from sqlalchemy import select
    from app.db.models import AnnotationRun
    other_run = db_session.scalar(select(AnnotationRun).where(AnnotationRun.job_id == "j-2"))

    app.dependency_overrides[get_db] = _override_db_factory(db_session)
    try:
        token = make_token(github_id=1, github_login="u1")
        r = TestClient(app).get(f"/api/v1/runs/{other_run.id}", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()
