from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: str
    dataset_id: str
    dataset_filename: str
    total_sessions: int
    completed_sessions: int
    status: str
    llm_config_snapshot: dict
    flagged_count: int
    resolved_count: int
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunListOut(BaseModel):
    items: list[RunOut]
    total: int
