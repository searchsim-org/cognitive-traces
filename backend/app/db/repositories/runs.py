"""Repository for annotation_runs."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import AnnotationRun

# Orchestrator emits `'completed' | 'stopped' | 'failed'`; the DB's
# annotation_runs.status column is documented as `running|paused|completed|failed`.
# Translate so we never persist a value outside the declared state machine.
_ORCHESTRATOR_STATUS_TO_DB = {
    "completed": "completed",
    "stopped": "paused",
    "failed": "failed",
    "running": "running",
    "paused": "paused",
}


def normalize_status(orchestrator_status: str) -> str:
    """Map an orchestrator-internal status onto the persisted enum."""
    return _ORCHESTRATOR_STATUS_TO_DB.get(orchestrator_status, "completed")


def create(
    db: Session,
    *,
    user_id: UUID,
    job_id: str,
    dataset_id: str,
    dataset_filename: str,
    total_sessions: int,
    llm_config_snapshot: dict,
) -> AnnotationRun:
    run = AnnotationRun(
        user_id=user_id,
        job_id=job_id,
        dataset_id=dataset_id,
        dataset_filename=dataset_filename,
        total_sessions=total_sessions,
        llm_config_snapshot=llm_config_snapshot,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()
    return run


def get(db: Session, job_id: str) -> Optional[AnnotationRun]:
    return db.scalar(select(AnnotationRun).where(AnnotationRun.job_id == job_id))


def list_for_user(db: Session, user_id: UUID, *, limit: int, offset: int) -> list[AnnotationRun]:
    return list(
        db.scalars(
            select(AnnotationRun)
            .where(AnnotationRun.user_id == user_id)
            .order_by(AnnotationRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )


def count_for_user(db: Session, user_id: UUID) -> int:
    from sqlalchemy import func
    return db.scalar(select(func.count(AnnotationRun.id)).where(AnnotationRun.user_id == user_id)) or 0


def delete(db: Session, run_id: UUID, user_id: UUID) -> bool:
    run = db.scalar(
        select(AnnotationRun).where(AnnotationRun.id == run_id, AnnotationRun.user_id == user_id)
    )
    if run is None:
        return False
    db.delete(run)
    db.flush()
    return True


def mark_status(db: Session, job_id: str, status: str) -> None:
    db.execute(update(AnnotationRun).where(AnnotationRun.job_id == job_id).values(status=status))


def mark_terminal(
    db: Session,
    job_id: str,
    *,
    status: str,
    completed_sessions: int,
    flagged_count: int,
    error_message: Optional[str] = None,
) -> None:
    """Persist a job's final state.

    `status` must already be normalized to the DB enum (see normalize_status).
    `flagged_count` is taken as the MAX of the stored value and the new one so
    a resumed run (whose orchestrator only tracks flags from the resumed
    sessions) cannot overwrite the accumulated total from earlier runs.
    `completed_sessions` uses the same MAX guard for the same reason.
    """
    db.execute(
        update(AnnotationRun)
        .where(AnnotationRun.job_id == job_id)
        .values(
            status=status,
            completed_sessions=func.greatest(
                AnnotationRun.completed_sessions, completed_sessions
            ),
            flagged_count=func.greatest(AnnotationRun.flagged_count, flagged_count),
            error_message=error_message,
            completed_at=datetime.now(timezone.utc),
        )
    )


def increment_resolved(db: Session, job_id: str) -> None:
    db.execute(
        update(AnnotationRun)
        .where(AnnotationRun.job_id == job_id)
        .values(resolved_count=AnnotationRun.resolved_count + 1)
    )


def persist_run_if_authed(
    db: Session,
    *,
    current_user,
    job_id: str,
    dataset_id: str,
    dataset_filename: str,
    total_sessions: int,
    llm_config: dict,
) -> bool:
    """Create an annotation_runs row when a user is present. No-op when anonymous.

    Idempotent on `job_id`: if a row already exists (e.g. /start-job called
    with a `resume_job_id` for a job we previously persisted, or a racing
    retry), returns False without raising on the unique constraint.

    Returns True if a row was inserted.
    """
    from app.services.config_sanitizer import strip_secrets

    if current_user is None:
        return False
    if get(db, job_id) is not None:
        return False
    create(
        db,
        user_id=current_user.id,
        job_id=job_id,
        dataset_id=dataset_id,
        dataset_filename=dataset_filename,
        total_sessions=total_sessions,
        llm_config_snapshot=strip_secrets(llm_config),
    )
    db.commit()
    return True
