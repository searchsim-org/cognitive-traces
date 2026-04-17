from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PresetIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    config_json: dict


class PresetPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    config_json: dict | None = None


class PresetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    config_json: dict
    created_at: datetime
    updated_at: datetime
