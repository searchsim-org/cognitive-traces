from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    github_id: int
    github_login: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    created_at: datetime
