#!/usr/bin/env python3
"""
Transformer-based models for session abandonment prediction.

Two model variants:
1. Behavioral-Only Baseline: S-BERT embeddings for queries and clicked documents
2. Cognitive-Enhanced: S-BERT embeddings + cognitive label embeddings
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class TransformerAbandonmentModel(nn.Module):
    """
    Transformer encoder model for session abandonment prediction.
    
    Architecture:
    - 4-layer Transformer encoder with 8 attention heads
    - [CLS] token at sequence start
    - Final [CLS] hidden state → Linear → Sigmoid
    
    Args:
        input_dim: Dimension of input event embeddings
        num_layers: Number of transformer layers (default: 4)
        num_heads: Number of attention heads (default: 8)
        hidden_dim: Hidden dimension of transformer (default: 768)
        dropout: Dropout probability (default: 0.1)
    """
    
    def __init__(
        self,
        input_dim: int,
        num_layers: int = 4,
        num_heads: int = 8,
        hidden_dim: int = 768,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Project input to hidden dimension if needed
        self.input_projection = nn.Linear(input_dim, hidden_dim) if input_dim != hidden_dim else nn.Identity()
        
        # Special [CLS] token embedding
        self.cls_token = nn.Parameter(torch.randn(1, 1, hidden_dim))
        
        # Positional encoding
        self.pos_encoding = PositionalEncoding(hidden_dim, dropout=dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Classification head
        self.classifier = nn.Linear(hidden_dim, 1)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights using Xavier uniform initialization."""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(
        self,
        event_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            event_embeddings: Shape (batch_size, seq_len, input_dim)
            attention_mask: Shape (batch_size, seq_len), 1 for valid tokens, 0 for padding
            
        Returns:
            logits: Shape (batch_size, 1) - abandonment probability logits
        """
        batch_size, seq_len, _ = event_embeddings.shape
        
        # Project to hidden dimension
        x = self.input_projection(event_embeddings)  # (batch, seq_len, hidden_dim)
        
        # Add [CLS] token
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)  # (batch, 1, hidden_dim)
        x = torch.cat([cls_tokens, x], dim=1)  # (batch, seq_len+1, hidden_dim)
        
        # Add positional encoding
        x = self.pos_encoding(x)
        
        # Update attention mask for [CLS] token
        if attention_mask is not None:
            cls_mask = torch.ones(batch_size, 1, device=attention_mask.device, dtype=attention_mask.dtype)
            attention_mask = torch.cat([cls_mask, attention_mask], dim=1)  # (batch, seq_len+1)
            # Convert to transformer format: 0 for valid, -inf for padding
            src_key_padding_mask = (attention_mask == 0)
        else:
            src_key_padding_mask = None
        
        # Transformer encoding
        x = self.transformer(x, src_key_padding_mask=src_key_padding_mask)  # (batch, seq_len+1, hidden_dim)
        
        # Extract [CLS] token representation
        cls_output = x[:, 0, :]  # (batch, hidden_dim)
        
        # Classification
        logits = self.classifier(cls_output)  # (batch, 1)
        
        return logits


class PositionalEncoding(nn.Module):
    """
    Positional encoding for transformer.
    Uses sinusoidal positional encoding.
    """
    
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # Create positional encoding
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe = torch.zeros(1, max_len, d_model)
        pe[0, :, 0::2] = torch.sin(position * div_term)
        pe[0, :, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Shape (batch, seq_len, d_model)
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class BehavioralOnlyModel(nn.Module):
    """
    Behavioral-Only Baseline Model.
    
    Event representation:
    - QUERY: S-BERT embedding of query text (768-dim)
    - CLICK: S-BERT embedding of first 256 tokens of document (768-dim)
    - SERP_VIEW (zero-click): Trainable embedding (768-dim)
    
    Args:
        num_layers: Number of transformer layers (default: 4)
        num_heads: Number of attention heads (default: 8)
        hidden_dim: Hidden dimension (default: 768)
        dropout: Dropout probability (default: 0.1)
    """
    
    def __init__(
        self,
        num_layers: int = 4,
        num_heads: int = 8,
        hidden_dim: int = 768,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        
        # Trainable embedding for zero-click events (SERP_VIEW with no subsequent CLICK)
        self.zero_click_embedding = nn.Parameter(torch.randn(1, hidden_dim))
        
        # Transformer model
        self.transformer_model = TransformerAbandonmentModel(
            input_dim=hidden_dim,  # S-BERT outputs 768-dim
            num_layers=num_layers,
            num_heads=num_heads,
            hidden_dim=hidden_dim,
            dropout=dropout
        )
    
    def forward(
        self,
        event_embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            event_embeddings: Shape (batch_size, seq_len, 768)
                             Pre-computed S-BERT embeddings for queries/docs
                             Zero vectors for SERP_VIEW events (will be replaced)
            attention_mask: Shape (batch_size, seq_len), 1 for valid, 0 for padding
            
        Returns:
            logits: Shape (batch_size, 1)
        """
        # Note: Zero-click embeddings should be filled in during data preprocessing
        # or we can identify them here if we have event type information
        return self.transformer_model(event_embeddings, attention_mask)


class CognitiveEnhancedModel(nn.Module):
    """
    Cognitive-Enhanced Model.
    
    Event representation:
    - S-BERT embedding (768-dim) for query/document content
    - Concatenated with cognitive label embedding (32-dim)
    - Total input: 800-dim
    
    Args:
        num_cognitive_labels: Number of cognitive labels
        cognitive_embedding_dim: Dimension of cognitive label embeddings (default: 32)
        num_layers: Number of transformer layers (default: 4)
        num_heads: Number of attention heads (default: 8)
        hidden_dim: Hidden dimension (default: 768)
        dropout: Dropout probability (default: 0.1)
    """
    
    def __init__(
        self,
        num_cognitive_labels: int,
        cognitive_embedding_dim: int = 32,
        num_layers: int = 4,
        num_heads: int = 8,
        hidden_dim: int = 768,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.cognitive_embedding_dim = cognitive_embedding_dim
        
        # Cognitive label embeddings
        self.cognitive_embeddings = nn.Embedding(num_cognitive_labels, cognitive_embedding_dim)
        
        # Trainable embedding for zero-click events
        self.zero_click_embedding = nn.Parameter(torch.randn(1, hidden_dim))
        
        # Input dimension: S-BERT (768) + cognitive label (32)
        input_dim = 768 + cognitive_embedding_dim
        
        # Transformer model
        self.transformer_model = TransformerAbandonmentModel(
            input_dim=input_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            hidden_dim=hidden_dim,
            dropout=dropout
        )
    
    def forward(
        self,
        event_embeddings: torch.Tensor,
        cognitive_label_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            event_embeddings: Shape (batch_size, seq_len, 768)
                             Pre-computed S-BERT embeddings
            cognitive_label_ids: Shape (batch_size, seq_len)
                                Cognitive label indices
            attention_mask: Shape (batch_size, seq_len), 1 for valid, 0 for padding
            
        Returns:
            logits: Shape (batch_size, 1)
        """
        # Get cognitive label embeddings
        cognitive_embs = self.cognitive_embeddings(cognitive_label_ids)  # (batch, seq_len, 32)
        
        # Concatenate behavioral and cognitive representations
        combined = torch.cat([event_embeddings, cognitive_embs], dim=-1)  # (batch, seq_len, 800)
        
        # Pass through transformer
        return self.transformer_model(combined, attention_mask)


def create_behavioral_model(
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
    **kwargs
) -> BehavioralOnlyModel:
    """
    Factory function to create behavioral-only model.
    
    Args:
        device: Device to place model on
        **kwargs: Additional arguments for BehavioralOnlyModel
        
    Returns:
        Initialized model on specified device
    """
    model = BehavioralOnlyModel(**kwargs)
    model = model.to(device)
    return model


def create_cognitive_model(
    num_cognitive_labels: int,
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
    **kwargs
) -> CognitiveEnhancedModel:
    """
    Factory function to create cognitive-enhanced model.
    
    Args:
        num_cognitive_labels: Number of cognitive labels in dataset
        device: Device to place model on
        **kwargs: Additional arguments for CognitiveEnhancedModel
        
    Returns:
        Initialized model on specified device
    """
    model = CognitiveEnhancedModel(num_cognitive_labels=num_cognitive_labels, **kwargs)
    model = model.to(device)
    return model


if __name__ == '__main__':
    # Test models
    print("Testing Behavioral-Only Model...")
    behavioral_model = create_behavioral_model(device='cpu')
    batch_size, seq_len = 4, 10
    event_embs = torch.randn(batch_size, seq_len, 768)
    mask = torch.ones(batch_size, seq_len)
    logits = behavioral_model(event_embs, mask)
    print(f"Output shape: {logits.shape}")
    print(f"Output: {logits}")
    
    print("\nTesting Cognitive-Enhanced Model...")
    cognitive_model = create_cognitive_model(num_cognitive_labels=20, device='cpu')
    cognitive_ids = torch.randint(0, 20, (batch_size, seq_len))
    logits = cognitive_model(event_embs, cognitive_ids, mask)
    print(f"Output shape: {logits.shape}")
    print(f"Output: {logits}")
    
    print("\nModels created successfully!")

