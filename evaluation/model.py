#!/usr/bin/env python3
"""
Transformer-based models for binary prediction tasks.

Three model variants:
1. Behavioral-Only Baseline: S-BERT embeddings + action_type embeddings
2. Cognitive-Enhanced: S-BERT + action_type + cognitive label embeddings
3. Shuffled-Label Ablation: Same as cognitive but randomly permutes labels (control)
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
    - S-BERT embedding (384-dim) for query/document/SERP content
    - Action type embedding (32-dim) for QUERY/CLICK/SERP_VIEW
    - Total input: 416-dim

    Args:
        num_action_types: Number of action types including PAD (default: 4)
        action_type_embedding_dim: Dimension of action type embeddings (default: 32)
        num_layers: Number of transformer layers (default: 4)
        num_heads: Number of attention heads (default: 8)
        hidden_dim: Hidden dimension (default: 768)
        dropout: Dropout probability (default: 0.1)
    """

    def __init__(
        self,
        input_dim: int = 384,
        num_action_types: int = 4,
        action_type_embedding_dim: int = 32,
        num_layers: int = 4,
        num_heads: int = 8,
        hidden_dim: int = 768,
        dropout: float = 0.1
    ):
        super().__init__()

        self.hidden_dim = hidden_dim

        # Action type embeddings: QUERY=0, CLICK=1, SERP_VIEW=2, PAD=3
        self.action_type_embeddings = nn.Embedding(num_action_types, action_type_embedding_dim)

        # Input dimension: S-BERT + action_type
        combined_input_dim = input_dim + action_type_embedding_dim

        # Transformer model
        self.transformer_model = TransformerAbandonmentModel(
            input_dim=combined_input_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            hidden_dim=hidden_dim,
            dropout=dropout
        )

    def forward(
        self,
        event_embeddings: torch.Tensor,
        action_type_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            event_embeddings: Shape (batch_size, seq_len, 384)
                             Pre-computed S-BERT embeddings
            action_type_ids: Shape (batch_size, seq_len)
                            Action type indices (0=QUERY, 1=CLICK, 2=SERP_VIEW, 3=PAD)
            attention_mask: Shape (batch_size, seq_len), 1 for valid, 0 for padding

        Returns:
            logits: Shape (batch_size, 1)
        """
        # Get action type embeddings
        action_embs = self.action_type_embeddings(action_type_ids)  # (batch, seq_len, 32)

        # Concatenate S-BERT and action type representations
        combined = torch.cat([event_embeddings, action_embs], dim=-1)  # (batch, seq_len, 416)

        return self.transformer_model(combined, attention_mask)


class CognitiveEnhancedModel(nn.Module):
    """
    Cognitive-Enhanced Model.

    Event representation:
    - S-BERT embedding (384-dim) for query/document/SERP content
    - Action type embedding (32-dim) for QUERY/CLICK/SERP_VIEW
    - Cognitive label embedding (32-dim) for IFT labels
    - Total input: 448-dim

    Args:
        num_cognitive_labels: Number of cognitive labels
        cognitive_embedding_dim: Dimension of cognitive label embeddings (default: 32)
        num_action_types: Number of action types including PAD (default: 4)
        action_type_embedding_dim: Dimension of action type embeddings (default: 32)
        num_layers: Number of transformer layers (default: 4)
        num_heads: Number of attention heads (default: 8)
        hidden_dim: Hidden dimension (default: 768)
        dropout: Dropout probability (default: 0.1)
    """

    def __init__(
        self,
        num_cognitive_labels: int,
        sbert_embedding_dim: int = 384,
        cognitive_embedding_dim: int = 32,
        num_action_types: int = 4,
        action_type_embedding_dim: int = 32,
        num_layers: int = 4,
        num_heads: int = 8,
        hidden_dim: int = 768,
        dropout: float = 0.1
    ):
        super().__init__()

        self.hidden_dim = hidden_dim
        self.cognitive_embedding_dim = cognitive_embedding_dim

        # Action type embeddings: QUERY=0, CLICK=1, SERP_VIEW=2, PAD=3
        self.action_type_embeddings = nn.Embedding(num_action_types, action_type_embedding_dim)

        # Cognitive label embeddings
        self.cognitive_embeddings = nn.Embedding(num_cognitive_labels, cognitive_embedding_dim)

        # Input dimension: S-BERT + action_type + cognitive label
        input_dim = sbert_embedding_dim + action_type_embedding_dim + cognitive_embedding_dim

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
        action_type_ids: torch.Tensor,
        cognitive_label_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            event_embeddings: Shape (batch_size, seq_len, 384)
                             Pre-computed S-BERT embeddings
            action_type_ids: Shape (batch_size, seq_len)
                            Action type indices
            cognitive_label_ids: Shape (batch_size, seq_len)
                                Cognitive label indices
            attention_mask: Shape (batch_size, seq_len), 1 for valid, 0 for padding

        Returns:
            logits: Shape (batch_size, 1)
        """
        # Get action type embeddings
        action_embs = self.action_type_embeddings(action_type_ids)  # (batch, seq_len, 32)

        # Get cognitive label embeddings
        cognitive_embs = self.cognitive_embeddings(cognitive_label_ids)  # (batch, seq_len, 32)

        # Concatenate all representations
        combined = torch.cat([event_embeddings, action_embs, cognitive_embs], dim=-1)  # (batch, seq_len, 448)

        # Pass through transformer
        return self.transformer_model(combined, attention_mask)


class ShuffledLabelModel(nn.Module):
    """
    Shuffled-Label Ablation Model.

    Same architecture as CognitiveEnhancedModel, but randomly permutes
    cognitive_label_ids within each non-padded sequence during forward().
    This tests whether the specific label assignments matter, or whether
    ANY categorical signal would produce similar improvements.

    Args:
        Same as CognitiveEnhancedModel
    """

    def __init__(
        self,
        num_cognitive_labels: int,
        sbert_embedding_dim: int = 384,
        cognitive_embedding_dim: int = 32,
        num_action_types: int = 4,
        action_type_embedding_dim: int = 32,
        num_layers: int = 4,
        num_heads: int = 8,
        hidden_dim: int = 768,
        dropout: float = 0.1
    ):
        super().__init__()

        self.hidden_dim = hidden_dim
        self.cognitive_embedding_dim = cognitive_embedding_dim

        # Action type embeddings
        self.action_type_embeddings = nn.Embedding(num_action_types, action_type_embedding_dim)

        # Cognitive label embeddings (same architecture, but labels will be shuffled)
        self.cognitive_embeddings = nn.Embedding(num_cognitive_labels, cognitive_embedding_dim)

        # Input dimension: S-BERT + action_type + cognitive label
        input_dim = sbert_embedding_dim + action_type_embedding_dim + cognitive_embedding_dim

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
        action_type_ids: torch.Tensor,
        cognitive_label_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass with shuffled cognitive labels.

        Randomly permutes cognitive_label_ids within each sequence's
        non-padded positions, destroying temporal label patterns
        while preserving label distribution.
        """
        batch_size, seq_len = cognitive_label_ids.shape

        # Shuffle cognitive labels within each sequence's valid positions
        shuffled_ids = cognitive_label_ids.clone()
        if attention_mask is not None:
            for i in range(batch_size):
                valid_len = int(attention_mask[i].sum().item())
                if valid_len > 1:
                    perm = torch.randperm(valid_len, device=cognitive_label_ids.device)
                    shuffled_ids[i, :valid_len] = cognitive_label_ids[i, perm]
        else:
            for i in range(batch_size):
                perm = torch.randperm(seq_len, device=cognitive_label_ids.device)
                shuffled_ids[i] = cognitive_label_ids[i, perm]

        # Get action type embeddings
        action_embs = self.action_type_embeddings(action_type_ids)

        # Get cognitive label embeddings (shuffled)
        cognitive_embs = self.cognitive_embeddings(shuffled_ids)

        # Concatenate all representations
        combined = torch.cat([event_embeddings, action_embs, cognitive_embs], dim=-1)

        return self.transformer_model(combined, attention_mask)


def create_behavioral_model(
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
    **kwargs
) -> BehavioralOnlyModel:
    """Factory function to create behavioral-only model."""
    model = BehavioralOnlyModel(**kwargs)
    model = model.to(device)
    return model


def create_cognitive_model(
    num_cognitive_labels: int,
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
    **kwargs
) -> CognitiveEnhancedModel:
    """Factory function to create cognitive-enhanced model."""
    model = CognitiveEnhancedModel(num_cognitive_labels=num_cognitive_labels, **kwargs)
    model = model.to(device)
    return model


def create_shuffled_model(
    num_cognitive_labels: int,
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
    **kwargs
) -> ShuffledLabelModel:
    """Factory function to create shuffled-label ablation model."""
    model = ShuffledLabelModel(num_cognitive_labels=num_cognitive_labels, **kwargs)
    model = model.to(device)
    return model


if __name__ == '__main__':
    batch_size, seq_len = 4, 10
    sbert_dim = 384
    event_embs = torch.randn(batch_size, seq_len, sbert_dim)
    action_ids = torch.randint(0, 3, (batch_size, seq_len))
    mask = torch.ones(batch_size, seq_len)

    print("Testing Behavioral-Only Model...")
    behavioral_model = create_behavioral_model(device='cpu')
    logits = behavioral_model(event_embs, action_ids, mask)
    print(f"  Output shape: {logits.shape}")
    print(f"  Parameters: {sum(p.numel() for p in behavioral_model.parameters()):,}")

    print("\nTesting Cognitive-Enhanced Model...")
    cognitive_model = create_cognitive_model(num_cognitive_labels=7, device='cpu')
    cognitive_ids = torch.randint(0, 7, (batch_size, seq_len))
    logits = cognitive_model(event_embs, action_ids, cognitive_ids, mask)
    print(f"  Output shape: {logits.shape}")
    print(f"  Parameters: {sum(p.numel() for p in cognitive_model.parameters()):,}")

    print("\nTesting Shuffled-Label Model...")
    shuffled_model = create_shuffled_model(num_cognitive_labels=7, device='cpu')
    logits = shuffled_model(event_embs, action_ids, cognitive_ids, mask)
    print(f"  Output shape: {logits.shape}")
    print(f"  Parameters: {sum(p.numel() for p in shuffled_model.parameters()):,}")

    print("\nAll models created successfully!")

