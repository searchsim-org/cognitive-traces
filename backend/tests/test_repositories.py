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


# --- status normalization + mark_terminal MAX guard (C1, C3 review fixes) ---

from app.db.repositories.runs import normalize_status, persist_run_if_authed


def test_normalize_status_maps_orchestrator_states_to_db_enum():
    # Orchestrator's vocabulary -> DB column's enum
    assert normalize_status("stopped") == "paused"
    assert normalize_status("completed") == "completed"
    assert normalize_status("failed") == "failed"
    # Pass-through for already-normalized values
    assert normalize_status("running") == "running"
    assert normalize_status("paused") == "paused"
    # Unknown states fall back to completed (safer than persisting garbage)
    assert normalize_status("weird-state") == "completed"


def test_mark_terminal_does_not_overwrite_larger_flagged_count(db_session):
    """A resumed run's flagged count is LOCAL to that run. The persisted total
    must never shrink back to a smaller per-run value."""
    u = _user(db_session)
    runs_create(
        db_session, user_id=u.id, job_id="j", dataset_id="d",
        dataset_filename="f", total_sessions=10, llm_config_snapshot={},
    )
    db_session.commit()

    # Initial run: 3 flagged
    mark_terminal(db_session, "j", status="completed", completed_sessions=5, flagged_count=3)
    db_session.commit()
    assert runs_get(db_session, "j").flagged_count == 3

    # Resumed run saw only 1 new flag (2 already in DB) — must NOT clobber down to 1
    mark_terminal(db_session, "j", status="completed", completed_sessions=10, flagged_count=1)
    db_session.commit()
    row = runs_get(db_session, "j")
    assert row.flagged_count == 3
    assert row.completed_sessions == 10  # this one advanced correctly


def test_persist_run_if_authed_is_idempotent_on_same_job_id(db_session):
    """/start-job called with resume_job_id for a logged-in user used to
    crash with IntegrityError. Now it's a no-op returning False."""
    u = _user(db_session)
    assert persist_run_if_authed(
        db_session, current_user=u, job_id="j", dataset_id="d",
        dataset_filename="f.csv", total_sessions=5, llm_config={"x": 1},
    ) is True
    # Second call with the same job_id no-ops
    assert persist_run_if_authed(
        db_session, current_user=u, job_id="j", dataset_id="d",
        dataset_filename="f.csv", total_sessions=5, llm_config={"x": 1},
    ) is False
    # Only one row exists
    from sqlalchemy import func as _sqlfunc, select as _sqlselect
    count = db_session.scalar(_sqlselect(_sqlfunc.count(AnnotationRun.id)))
    assert count == 1
