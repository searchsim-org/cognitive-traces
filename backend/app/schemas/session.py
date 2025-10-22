"""
Pydantic schemas for session data
"""

from pydantic import BaseModel
from typing import List, Optional
from app.schemas.annotation import AnnotatedEvent


class SessionResponse(BaseModel):
    """Response containing session details"""
    session_id: str
    dataset: str
    user_id: Optional[str] = None
    start_time: str
    end_time: str
    num_events: int
    annotated_events: List[AnnotatedEvent]


class SessionSummary(BaseModel):
    """Summary of a session for list views"""
    session_id: str
    dataset: str
    num_events: int
    start_time: str
    has_annotations: bool


class SessionListResponse(BaseModel):
    """Response for paginated session list"""
    sessions: List[SessionSummary]
    total: int
    skip: int
    limit: int

