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


class SessionHandlingStrategy(str, Enum):
    """Strategy for handling long sessions"""
    TRUNCATE = "truncate"
    SLIDING_WINDOW = "sliding_window"
    FULL = "full"


class LLMConfigSchema(BaseModel):
    """Configuration for LLM agents"""
    
    # Model selection
    analyst_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model for analyst agent"
    )
    critic_model: str = Field(
        default="gpt-4o",
        description="Model for critic agent"
    )
    judge_model: str = Field(
        default="gpt-4o",
        description="Model for judge agent"
    )
    
    # API keys
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    google_api_key: Optional[str] = Field(None, description="Google API key")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL for local models"
    )
    
    # Custom endpoints
    custom_endpoints: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Custom OpenAI-compatible LLM endpoints"
    )
    
    # Fallback configuration
    enable_fallback: bool = Field(
        default=False,
        description="Enable fallback to commercial models when custom endpoint fails"
    )
    fallback_analyst_model: str = Field(
        default="gpt-4o-mini",
        description="Fallback model for analyst agent"
    )
    fallback_critic_model: str = Field(
        default="gpt-4o-mini",
        description="Fallback model for critic agent"
    )
    fallback_judge_model: str = Field(
        default="gpt-4o-mini",
        description="Fallback model for judge agent"
    )
    fallback_retry_after: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Minutes to wait before retrying custom endpoint after failure"
    )
    
    # Session handling
    session_strategy: SessionHandlingStrategy = Field(
        default=SessionHandlingStrategy.TRUNCATE,
        description="How to handle long sessions"
    )
    window_size: int = Field(
        default=30,
        ge=5,
        le=100,
        description="Number of events for sliding window strategy"
    )
    
    # Model parameters
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for generation (0.0-2.0)"
    )
    max_tokens_base: int = Field(
        default=4096,
        ge=1024,
        le=32000,
        description="Base max tokens for generation"
    )
    max_tokens_cap: int = Field(
        default=16000,
        ge=4096,
        le=32000,
        description="Maximum cap for token scaling"
    )
    tokens_per_event: int = Field(
        default=100,
        ge=50,
        le=500,
        description="Additional tokens per event for scaling"
    )
    
    # Truncation limits (for TRUNCATE strategy)
    truncate_content_small: int = Field(
        default=200,
        ge=50,
        le=1000,
        description="Content chars for ≤20 events"
    )
    truncate_content_medium: int = Field(
        default=150,
        ge=50,
        le=1000,
        description="Content chars for 21-50 events"
    )
    truncate_content_large: int = Field(
        default=100,
        ge=50,
        le=1000,
        description="Content chars for >50 events"
    )
    truncate_reasoning_small: int = Field(
        default=300,
        ge=100,
        le=1000,
        description="Reasoning chars for ≤20 events"
    )
    truncate_reasoning_medium: int = Field(
        default=200,
        ge=100,
        le=1000,
        description="Reasoning chars for 21-50 events"
    )
    truncate_reasoning_large: int = Field(
        default=150,
        ge=100,
        le=1000,
        description="Reasoning chars for >50 events"
    )
    
    # Custom prompts (optional)
    analyst_prompt_override: Optional[str] = Field(
        None,
        description="Custom prompt for analyst agent (overrides default)"
    )
    critic_prompt_override: Optional[str] = Field(
        None,
        description="Custom prompt for critic agent (overrides default)"
    )
    judge_prompt_override: Optional[str] = Field(
        None,
        description="Custom prompt for judge agent (overrides default)"
    )

