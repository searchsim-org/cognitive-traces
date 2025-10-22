"""
Pydantic schemas for model information and predictions
"""

from pydantic import BaseModel
from typing import List, Dict
from app.schemas.annotation import EventData, CognitiveLabel


class ModelInfo(BaseModel):
    """Information about the pre-trained model"""
    model_name: str
    version: str
    architecture: str
    input_dim: int
    labels: List[str]
    training_data: str
    performance: Dict[str, float]


class PredictionRequest(BaseModel):
    """Request for model prediction"""
    session_id: str
    events: List[EventData]


class EventPrediction(BaseModel):
    """Predicted label for an event"""
    event_id: str
    predicted_label: CognitiveLabel
    confidence: float


class PredictionResponse(BaseModel):
    """Response containing predictions"""
    session_id: str
    predictions: List[EventPrediction]
    processing_time: float

