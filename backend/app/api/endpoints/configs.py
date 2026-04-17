from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.models import User
from app.db.repositories import presets as presets_repo
from app.db.session import get_db
from app.schemas.preset import PresetIn, PresetOut, PresetPatch

router = APIRouter()


@router.get("", response_model=list[PresetOut])
def list_presets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return presets_repo.list_for_user(db, user.id)


@router.post("", response_model=PresetOut, status_code=status.HTTP_201_CREATED)
def create_preset(payload: PresetIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        preset = presets_repo.create(
            db, user_id=user.id, name=payload.name, description=payload.description, config_json=payload.config_json
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Preset name already exists")
    return preset


@router.get("/{preset_id}", response_model=PresetOut)
def get_preset(preset_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preset = presets_repo.get(db, preset_id, user.id)
    if preset is None:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@router.patch("/{preset_id}", response_model=PresetOut)
def update_preset(preset_id: UUID, payload: PresetPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preset = presets_repo.get(db, preset_id, user.id)
    if preset is None:
        raise HTTPException(status_code=404, detail="Preset not found")
    try:
        preset = presets_repo.update(db, preset, name=payload.name, description=payload.description, config_json=payload.config_json)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Preset name already exists")
    return preset


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preset(preset_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preset = presets_repo.get(db, preset_id, user.id)
    if preset is None:
        raise HTTPException(status_code=404, detail="Preset not found")
    presets_repo.delete(db, preset)
    db.commit()
    return Response(status_code=204)
