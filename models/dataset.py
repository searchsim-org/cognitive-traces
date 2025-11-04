#!/usr/bin/env python3
"""
Dataset class for session abandonment prediction.

Handles:
- Loading preprocessed session data
- Computing S-BERT embeddings for queries and documents
- Creating batches with proper padding
- Cognitive label encoding
"""

import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
from sentence_transformers import SentenceTransformer
from collections import defaultdict


class SessionAbandonmentDataset(Dataset):
    """
    Dataset for session abandonment prediction.
    
    Args:
        csv_file: Path to CSV file with session data
        labels_file: Path to JSON file with session labels
        sbert_model_name: Name of S-BERT model (default: 'all-MiniLM-L6-v2')
        max_seq_len: Maximum sequence length (default: 50)
        cache_embeddings: Whether to cache S-BERT embeddings (default: True)
        cache_dir: Directory to cache embeddings (default: None)
        include_cognitive: Whether to include cognitive labels (default: False)
    """
    
    def __init__(
        self,
        csv_file: str,
        labels_file: str,
        sbert_model_name: str = 'all-MiniLM-L6-v2',
        max_seq_len: int = 50,
        cache_embeddings: bool = True,
        cache_dir: Optional[str] = None,
        include_cognitive: bool = False
    ):
        self.csv_file = csv_file
        self.labels_file = labels_file
        self.max_seq_len = max_seq_len
        self.include_cognitive = include_cognitive
        
        # Load data
        print(f"Loading data from {csv_file}...")
        self.df = pd.read_csv(csv_file)
        
        # Load labels
        with open(labels_file, 'r') as f:
            self.session_labels = json.load(f)
        
        # Group events by session
        self.sessions = self._group_sessions()
        self.session_ids = list(self.sessions.keys())
        
        print(f"Loaded {len(self.session_ids)} sessions")
        
        # Load S-BERT model
        print(f"Loading S-BERT model: {sbert_model_name}...")
        self.sbert_model = SentenceTransformer(sbert_model_name)
        self.embedding_dim = self.sbert_model.get_sentence_embedding_dimension()
        print(f"S-BERT embedding dimension: {self.embedding_dim}")
        
        # Setup caching
        self.cache_embeddings = cache_embeddings
        self.embedding_cache = {}
        
        if cache_dir:
            self.cache_path = Path(cache_dir)
            self.cache_path.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_path = None
        
        # Build cognitive label vocabulary if needed
        if include_cognitive:
            self.cognitive_label_to_id, self.id_to_cognitive_label = self._build_cognitive_vocab()
            print(f"Number of cognitive labels: {len(self.cognitive_label_to_id)}")
    
    def _group_sessions(self) -> Dict[str, pd.DataFrame]:
        """Group events by session ID."""
        sessions = {}
        for session_id, group in self.df.groupby('session_id'):
            # Sort by timestamp
            group = group.sort_values('event_timestamp')
            sessions[session_id] = group
        return sessions
    
    def _build_cognitive_vocab(self) -> Tuple[Dict[str, int], Dict[int, str]]:
        """Build vocabulary for cognitive labels."""
        # Get unique cognitive labels
        unique_labels = sorted(self.df['cognitive_label'].dropna().unique())
        
        # Create mappings
        label_to_id = {label: idx for idx, label in enumerate(unique_labels)}
        id_to_label = {idx: label for label, idx in label_to_id.items()}
        
        # Add special token for missing/unknown labels
        label_to_id['<UNK>'] = len(label_to_id)
        id_to_label[len(id_to_label)] = '<UNK>'
        
        return label_to_id, id_to_label
    
    def _get_content_text(self, row: pd.Series) -> str:
        """Extract text content from event."""
        action_type = row['action_type']
        content = row['content']
        
        if pd.isna(content):
            return ""
        
        # Content might be JSON string or plain text
        if isinstance(content, str):
            # Try to parse as JSON
            try:
                import json as json_lib
                content_dict = json_lib.loads(content)
                if 'query' in content_dict:
                    return content_dict['query']
                elif 'title' in content_dict:
                    return content_dict['title']
                elif 'text' in content_dict:
                    # For clicked documents, use first 256 tokens
                    text = content_dict['text']
                    tokens = text.split()[:256]
                    return ' '.join(tokens)
            except:
                pass
            
            # Return as is
            return content
        
        return str(content)
    
    def _compute_event_embedding(self, row: pd.Series) -> np.ndarray:
        """
        Compute S-BERT embedding for an event.
        
        For QUERY: Encode query text
        For CLICK: Encode first 256 tokens of document
        For SERP_VIEW: Return zero vector (will use trainable embedding)
        """
        action_type = row['action_type']
        
        # Zero vector for SERP_VIEW (zero-click events)
        if action_type == 'SERP_VIEW':
            return np.zeros(self.embedding_dim)
        
        # Get text content
        text = self._get_content_text(row)
        
        # Check cache
        cache_key = f"{action_type}:{text}"
        if self.cache_embeddings and cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Compute embedding
        if text:
            embedding = self.sbert_model.encode(text, convert_to_numpy=True)
        else:
            embedding = np.zeros(self.embedding_dim)
        
        # Cache
        if self.cache_embeddings:
            self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def _process_session(self, session_df: pd.DataFrame) -> Dict[str, torch.Tensor]:
        """
        Process a single session into model inputs.
        
        Returns:
            Dictionary with:
            - event_embeddings: (seq_len, 768)
            - attention_mask: (seq_len,)
            - cognitive_label_ids: (seq_len,) [if include_cognitive]
            - label: scalar (0 or 1)
        """
        # Limit sequence length
        if len(session_df) > self.max_seq_len:
            session_df = session_df.iloc[:self.max_seq_len]
        
        seq_len = len(session_df)
        
        # Compute event embeddings
        embeddings = []
        for _, row in session_df.iterrows():
            emb = self._compute_event_embedding(row)
            embeddings.append(emb)
        
        embeddings = np.array(embeddings)  # (seq_len, 768)
        
        # Create attention mask (all 1s for actual events)
        attention_mask = np.ones(seq_len)
        
        # Get label
        session_id = session_df.iloc[0]['session_id']
        label = self.session_labels[session_id]
        
        result = {
            'event_embeddings': torch.FloatTensor(embeddings),
            'attention_mask': torch.FloatTensor(attention_mask),
            'label': torch.FloatTensor([label]),
            'session_id': session_id
        }
        
        # Add cognitive labels if needed
        if self.include_cognitive:
            cognitive_ids = []
            for _, row in session_df.iterrows():
                label_str = row.get('cognitive_label', '<UNK>')
                if pd.isna(label_str):
                    label_str = '<UNK>'
                label_id = self.cognitive_label_to_id.get(label_str, self.cognitive_label_to_id['<UNK>'])
                cognitive_ids.append(label_id)
            
            result['cognitive_label_ids'] = torch.LongTensor(cognitive_ids)
        
        return result
    
    def __len__(self) -> int:
        return len(self.session_ids)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        session_id = self.session_ids[idx]
        session_df = self.sessions[session_id]
        return self._process_session(session_df)


def collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """
    Collate function for DataLoader.
    Pads sequences to the same length within a batch.
    """
    # Find max sequence length in batch
    max_len = max(item['event_embeddings'].size(0) for item in batch)
    
    batch_size = len(batch)
    embedding_dim = batch[0]['event_embeddings'].size(1)
    include_cognitive = 'cognitive_label_ids' in batch[0]
    
    # Initialize padded tensors
    event_embeddings = torch.zeros(batch_size, max_len, embedding_dim)
    attention_mask = torch.zeros(batch_size, max_len)
    labels = torch.zeros(batch_size, 1)
    
    if include_cognitive:
        cognitive_label_ids = torch.zeros(batch_size, max_len, dtype=torch.long)
    
    session_ids = []
    
    # Fill in the data
    for i, item in enumerate(batch):
        seq_len = item['event_embeddings'].size(0)
        
        event_embeddings[i, :seq_len] = item['event_embeddings']
        attention_mask[i, :seq_len] = item['attention_mask']
        labels[i] = item['label']
        session_ids.append(item['session_id'])
        
        if include_cognitive:
            cognitive_label_ids[i, :seq_len] = item['cognitive_label_ids']
    
    result = {
        'event_embeddings': event_embeddings,
        'attention_mask': attention_mask,
        'labels': labels,
        'session_ids': session_ids
    }
    
    if include_cognitive:
        result['cognitive_label_ids'] = cognitive_label_ids
    
    return result


def create_dataloaders(
    data_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    sbert_model_name: str = 'all-MiniLM-L6-v2',
    max_seq_len: int = 50,
    include_cognitive: bool = False
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Create train, validation, and test dataloaders.
    
    Args:
        data_dir: Directory containing processed data
        batch_size: Batch size for training
        num_workers: Number of worker processes for data loading
        sbert_model_name: S-BERT model name
        max_seq_len: Maximum sequence length
        include_cognitive: Whether to include cognitive labels
        
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    data_path = Path(data_dir)
    
    # Create datasets
    train_dataset = SessionAbandonmentDataset(
        csv_file=str(data_path / 'train.csv'),
        labels_file=str(data_path / 'session_labels.json'),
        sbert_model_name=sbert_model_name,
        max_seq_len=max_seq_len,
        cache_embeddings=True,
        cache_dir=str(data_path / 'embedding_cache'),
        include_cognitive=include_cognitive
    )
    
    val_dataset = SessionAbandonmentDataset(
        csv_file=str(data_path / 'val.csv'),
        labels_file=str(data_path / 'session_labels.json'),
        sbert_model_name=sbert_model_name,
        max_seq_len=max_seq_len,
        cache_embeddings=True,
        cache_dir=str(data_path / 'embedding_cache'),
        include_cognitive=include_cognitive
    )
    
    test_dataset = SessionAbandonmentDataset(
        csv_file=str(data_path / 'test.csv'),
        labels_file=str(data_path / 'session_labels.json'),
        sbert_model_name=sbert_model_name,
        max_seq_len=max_seq_len,
        cache_embeddings=True,
        cache_dir=str(data_path / 'embedding_cache'),
        include_cognitive=include_cognitive
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=True
    )
    
    # Get number of cognitive labels for model initialization
    num_cognitive_labels = None
    if include_cognitive:
        num_cognitive_labels = len(train_dataset.cognitive_label_to_id)
    
    return train_loader, val_loader, test_loader, num_cognitive_labels


if __name__ == '__main__':
    # Test dataset loading
    print("Testing dataset loading...")
    
    # This requires preprocessed data to exist
    try:
        train_loader, val_loader, test_loader, num_labels = create_dataloaders(
            data_dir='models/data/processed',
            batch_size=4,
            num_workers=0,
            include_cognitive=True
        )
        
        print(f"\nDataloaders created:")
        print(f"  Train batches: {len(train_loader)}")
        print(f"  Val batches: {len(val_loader)}")
        print(f"  Test batches: {len(test_loader)}")
        print(f"  Cognitive labels: {num_labels}")
        
        # Test one batch
        batch = next(iter(train_loader))
        print(f"\nSample batch:")
        print(f"  Event embeddings shape: {batch['event_embeddings'].shape}")
        print(f"  Attention mask shape: {batch['attention_mask'].shape}")
        print(f"  Labels shape: {batch['labels'].shape}")
        if 'cognitive_label_ids' in batch:
            print(f"  Cognitive label IDs shape: {batch['cognitive_label_ids'].shape}")
        
    except Exception as e:
        print(f"Could not test dataloaders: {e}")
        print("This is expected if preprocessed data doesn't exist yet.")

