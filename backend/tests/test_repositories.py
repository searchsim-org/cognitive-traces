from app.db.repositories.users import upsert_by_github_id


def test_upsert_creates_then_updates(db_session):
    claims = {"github_id": 42, "github_login": "ada", "name": "Ada", "email": "a@x", "avatar_url": "http://a"}
    u1 = upsert_by_github_id(db_session, claims)
    db_session.commit()
    assert u1.github_id == 42
    assert u1.github_login == "ada"

    claims2 = {**claims, "name": "Ada L.", "avatar_url": "http://b"}
    u2 = upsert_by_github_id(db_session, claims2)
    db_session.commit()

    assert u1.id == u2.id
    assert u2.name == "Ada L."
    assert u2.avatar_url == "http://b"


from datetime import datetime

from app.db.models import AnnotationRun
from app.db.repositories.runs import (
    create as runs_create,
    delete as runs_delete,
    get as runs_get,
    increment_resolved,
    list_for_user,
    mark_status,
    mark_terminal,
)


def _user(db_session):
    from app.db.repositories.users import upsert_by_github_id
    u = upsert_by_github_id(
        db_session,
        {"github_id": 1, "github_login": "u", "name": None, "email": None, "avatar_url": None},
    )
    db_session.commit()
    return u


def test_create_and_get_by_job_id(db_session):
    u = _user(db_session)
    run = runs_create(
        db_session,
        user_id=u.id,
        job_id="job-abc",
        dataset_id="ds-1",
        dataset_filename="f.csv",
        total_sessions=10,
        llm_config_snapshot={"analyst_model": "x"},
    )
    db_session.commit()
    assert run.status == "running"
    assert runs_get(db_session, "job-abc").id == run.id


def test_mark_terminal_is_no_op_when_no_row(db_session):
    mark_terminal(db_session, "missing-job", status="completed", completed_sessions=0, flagged_count=0)
    db_session.commit()  # must not raise


def test_increment_resolved(db_session):
    u = _user(db_session)
    runs_create(db_session, user_id=u.id, job_id="j", dataset_id="d", dataset_filename="f", total_sessions=1, llm_config_snapshot={})
    db_session.commit()
    increment_resolved(db_session, "j")
    increment_resolved(db_session, "j")
    db_session.commit()
    assert runs_get(db_session, "j").resolved_count == 2


def test_list_for_user_returns_newest_first(db_session):
    u = _user(db_session)
    runs_create(db_session, user_id=u.id, job_id="a", dataset_id="d", dataset_filename="f", total_sessions=1, llm_config_snapshot={})
    runs_create(db_session, user_id=u.id, job_id="b", dataset_id="d", dataset_filename="f", total_sessions=1, llm_config_snapshot={})
    db_session.commit()
    ids = [r.job_id for r in list_for_user(db_session, u.id, limit=10, offset=0)]
    assert ids == ["b", "a"]
