"""
Pydantic schemas for annotation requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class CognitiveLabel(str, Enum):
    """Cognitive labels based on Information Foraging Theory"""
    FOLLOWING_SCENT = "FollowingScent"
    APPROACHING_SOURCE = "ApproachingSource"
    DIET_ENRICHMENT = "DietEnrichment"
    POOR_SCENT = "PoorScent"
    LEAVING_PATCH = "LeavingPatch"
    FORAGING_SUCCESS = "ForagingSuccess"


class EventData(BaseModel):
    """Individual event in a user session"""
    event_id: str
    timestamp: str
    action_type: str = Field(..., description="Type of action: QUERY, CLICK, RATE, etc.")
    content: str = Field(..., description="Query text, document content, etc.")
    metadata: Optional[Dict[str, Any]] = None


class AnnotationRequest(BaseModel):
    """Request to annotate a single session"""
    session_id: str
    events: List[EventData]
    dataset_type: str = Field(default="custom", description="aol, stackoverflow, movielens, or custom")
    use_full_pipeline: bool = Field(default=True, description="Use multi-agent framework (slower, more accurate) vs pre-trained model")


class AgentDecision(BaseModel):
    """Decision made by an agent in the multi-agent framework"""
    agent_name: str = Field(..., description="analyst, critic, or judge")
    label: CognitiveLabel
    justification: str
    confidence: Optional[float] = None


class AnnotatedEvent(BaseModel):
    """Event with cognitive annotation"""
    event_id: str
    cognitive_label: CognitiveLabel
    agent_decisions: List[AgentDecision] = Field(
        ..., 
        description="Decisions from Analyst, Critic, and Judge"
    )
    final_justification: str
    confidence_score: float


class AnnotationResponse(BaseModel):
    """Response containing annotated session"""
    session_id: str
    annotated_events: List[AnnotatedEvent]
    processing_time: float = Field(..., description="Time in seconds")
    flagged_for_review: bool = Field(
        default=False, 
        description="True if disagreement threshold exceeded (top 1%)"
    )


class BatchAnnotationRequest(BaseModel):
    """Request for batch annotation"""
    sessions: List[AnnotationRequest]
    priority: int = Field(default=0, description="Higher priority jobs processed first")

