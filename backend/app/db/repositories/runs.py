"""Repository for annotation_runs."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import AnnotationRun


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
    db.execute(
        update(AnnotationRun)
        .where(AnnotationRun.job_id == job_id)
        .values(
            status=status,
            completed_sessions=completed_sessions,
            flagged_count=flagged_count,
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
