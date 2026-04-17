from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LlmConfigPreset
from app.services.config_sanitizer import strip_secrets


def list_for_user(db: Session, user_id: UUID) -> list[LlmConfigPreset]:
    return list(
        db.scalars(
            select(LlmConfigPreset)
            .where(LlmConfigPreset.user_id == user_id)
            .order_by(LlmConfigPreset.updated_at.desc())
        )
    )


def get(db: Session, preset_id: UUID, user_id: UUID) -> Optional[LlmConfigPreset]:
    return db.scalar(
        select(LlmConfigPreset).where(
            LlmConfigPreset.id == preset_id, LlmConfigPreset.user_id == user_id
        )
    )


def create(db: Session, *, user_id: UUID, name: str, description: Optional[str], config_json: dict) -> LlmConfigPreset:
    preset = LlmConfigPreset(
        user_id=user_id, name=name, description=description, config_json=strip_secrets(config_json)
    )
    db.add(preset)
    db.flush()
    return preset


def update(db: Session, preset: LlmConfigPreset, *, name: Optional[str], description: Optional[str], config_json: Optional[dict]) -> LlmConfigPreset:
    if name is not None:
        preset.name = name
    if description is not None:
        preset.description = description
    if config_json is not None:
        preset.config_json = strip_secrets(config_json)
    db.flush()
    return preset


def delete(db: Session, preset: LlmConfigPreset) -> None:
    db.delete(preset)
    db.flush()
