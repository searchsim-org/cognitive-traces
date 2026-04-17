from sqlalchemy import select

from app.db.models import AnnotationRun
from app.db.repositories.runs import persist_run_if_authed
from app.db.repositories.users import upsert_by_github_id


def test_persist_when_anonymous_is_noop(db_session):
    assert persist_run_if_authed(
        db_session,
        current_user=None,
        job_id="j1",
        dataset_id="d1",
        dataset_filename="f.csv",
        total_sessions=5,
        llm_config={"anthropic_api_key": "secret", "analyst_model": "m"},
    ) is False
    assert db_session.scalar(select(AnnotationRun)) is None


def test_persist_when_authed_writes_row_with_secrets_stripped(db_session):
    u = upsert_by_github_id(
        db_session,
        {"github_id": 1, "github_login": "u", "name": None, "email": None, "avatar_url": None},
    )
    db_session.commit()
    assert persist_run_if_authed(
        db_session,
        current_user=u,
        job_id="j1",
        dataset_id="d1",
        dataset_filename="f.csv",
        total_sessions=5,
        llm_config={"anthropic_api_key": "secret", "analyst_model": "m"},
    ) is True
    row = db_session.scalar(select(AnnotationRun))
    assert row is not None
    assert row.job_id == "j1"
    assert row.total_sessions == 5
    assert "anthropic_api_key" not in row.llm_config_snapshot
    assert row.llm_config_snapshot["analyst_model"] == "m"
    assert row.status == "running"
