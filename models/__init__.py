"""
Session Abandonment Prediction Models

This package implements Transformer-based models for predicting
session abandonment in search sessions.

Models:
- Behavioral-Only Baseline: Uses S-BERT embeddings
- Cognitive-Enhanced: Augments with cognitive trace labels
"""

from .model import (
    TransformerAbandonmentModel,
    BehavioralOnlyModel,
    CognitiveEnhancedModel,
    create_behavioral_model,
    create_cognitive_model
)

from .dataset import (
    SessionAbandonmentDataset,
    create_dataloaders
)

from .evaluate import (
    compute_metrics,
    evaluate_model
)

__version__ = '1.0.0'

__all__ = [
    'TransformerAbandonmentModel',
    'BehavioralOnlyModel',
    'CognitiveEnhancedModel',
    'create_behavioral_model',
    'create_cognitive_model',
    'SessionAbandonmentDataset',
    'create_dataloaders',
    'compute_metrics',
    'evaluate_model',
]

