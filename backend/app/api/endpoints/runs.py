from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.models import User
from app.db.repositories import runs as runs_repo
from app.db.session import get_db
from app.schemas.run import RunListOut, RunOut

router = APIRouter()


@router.get("", response_model=RunListOut)
def list_runs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = runs_repo.list_for_user(db, user.id, limit=limit, offset=offset)
    total = runs_repo.count_for_user(db, user.id)
    return RunListOut(items=[RunOut.model_validate(r) for r in items], total=total)


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import select
    from app.db.models import AnnotationRun
    run = db.scalar(select(AnnotationRun).where(AnnotationRun.id == run_id, AnnotationRun.user_id == user.id))
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ok = runs_repo.delete(db, run_id, user.id)
    db.commit()
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return Response(status_code=204)
