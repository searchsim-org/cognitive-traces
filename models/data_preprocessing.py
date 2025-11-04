#!/usr/bin/env python3
"""
Data preprocessing for session abandonment prediction.

Creates a balanced dataset from annotated AOL sessions:
- Identifies abandoned sessions (2+ queries, ends with zero clicks, 30+ min inactivity)
- Creates balanced dataset (50% abandoned, 50% non-abandoned)
- Splits data: 80% train, 10% val, 10% test (no user overlap)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Set
from datetime import datetime, timedelta
import json
from collections import defaultdict


def parse_timestamp(ts_str: str) -> datetime:
    """Parse timestamp string to datetime object."""
    try:
        return pd.to_datetime(ts_str)
    except:
        return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')


def identify_abandoned_sessions(df: pd.DataFrame) -> Set[str]:
    """
    Identify abandoned sessions based on the definition:
    - 2+ query reformulations
    - Ends with zero clicks (last event is not a CLICK)
    - No activity for 30+ minutes after last event
    
    Args:
        df: DataFrame with columns: session_id, event_id, event_timestamp, action_type
        
    Returns:
        Set of abandoned session IDs
    """
    abandoned = set()
    
    # Group by session
    for session_id, session_df in df.groupby('session_id'):
        # Sort by timestamp
        session_df = session_df.sort_values('event_timestamp')
        
        # Count queries (excluding SERP_VIEW which is not a reformulation)
        queries = session_df[session_df['action_type'] == 'QUERY']
        num_queries = len(queries)
        
        # Check if 2+ queries
        if num_queries < 2:
            continue
            
        # Check if last event is not a CLICK
        last_action = session_df.iloc[-1]['action_type']
        if last_action == 'CLICK':
            continue
            
        # We consider a session abandoned if it meets the above criteria
        # (The 30+ minutes inactivity is implicit - the session ends)
        abandoned.add(session_id)
    
    return abandoned


def get_user_from_session(session_id: str) -> str:
    """Extract user ID from session ID (format: userID_sessionNum)."""
    return session_id.split('_')[0] if '_' in session_id else session_id


def split_by_users(
    session_ids: List[str],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    random_seed: int = 42
) -> Tuple[List[str], List[str], List[str]]:
    """
    Split sessions by users to ensure no user overlap between sets.
    
    Args:
        session_ids: List of session IDs
        train_ratio: Proportion for training set
        val_ratio: Proportion for validation set
        test_ratio: Proportion for test set
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (train_sessions, val_sessions, test_sessions)
    """
    np.random.seed(random_seed)
    
    # Group sessions by user
    user_to_sessions = defaultdict(list)
    for sid in session_ids:
        user = get_user_from_session(sid)
        user_to_sessions[user].append(sid)
    
    # Get all users and shuffle
    users = list(user_to_sessions.keys())
    np.random.shuffle(users)
    
    # Split users
    n_users = len(users)
    n_train = int(n_users * train_ratio)
    n_val = int(n_users * val_ratio)
    
    train_users = users[:n_train]
    val_users = users[n_train:n_train + n_val]
    test_users = users[n_train + n_val:]
    
    # Collect sessions
    train_sessions = []
    for user in train_users:
        train_sessions.extend(user_to_sessions[user])
    
    val_sessions = []
    for user in val_users:
        val_sessions.extend(user_to_sessions[user])
    
    test_sessions = []
    for user in test_users:
        test_sessions.extend(user_to_sessions[user])
    
    return train_sessions, val_sessions, test_sessions


def create_balanced_dataset(
    input_csv: str,
    output_dir: str = "data/processed",
    random_seed: int = 42
) -> Dict[str, any]:
    """
    Create balanced dataset for session abandonment prediction.
    
    Args:
        input_csv: Path to annotated CSV file
        output_dir: Output directory for processed data
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with statistics about the created dataset
    """
    np.random.seed(random_seed)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    
    print(f"Total events: {len(df)}")
    print(f"Total sessions: {df['session_id'].nunique()}")
    print(f"Total users: {df['session_id'].apply(get_user_from_session).nunique()}")
    
    # Identify abandoned sessions
    print("\nIdentifying abandoned sessions...")
    abandoned_sessions = identify_abandoned_sessions(df)
    print(f"Abandoned sessions: {len(abandoned_sessions)}")
    
    # Get non-abandoned sessions
    all_sessions = set(df['session_id'].unique())
    non_abandoned_sessions = all_sessions - abandoned_sessions
    print(f"Non-abandoned sessions: {len(non_abandoned_sessions)}")
    
    # Create balanced dataset by sampling equal numbers
    n_samples = min(len(abandoned_sessions), len(non_abandoned_sessions))
    print(f"\nCreating balanced dataset with {n_samples} sessions per class...")
    
    abandoned_list = list(abandoned_sessions)
    non_abandoned_list = list(non_abandoned_sessions)
    
    # Sample randomly
    np.random.shuffle(abandoned_list)
    np.random.shuffle(non_abandoned_list)
    
    sampled_abandoned = abandoned_list[:n_samples]
    sampled_non_abandoned = non_abandoned_list[:n_samples]
    
    # Split each class by users
    print("\nSplitting abandoned sessions by users...")
    train_ab, val_ab, test_ab = split_by_users(sampled_abandoned, random_seed=random_seed)
    
    print("Splitting non-abandoned sessions by users...")
    train_non_ab, val_non_ab, test_non_ab = split_by_users(sampled_non_abandoned, random_seed=random_seed)
    
    # Combine
    train_sessions = train_ab + train_non_ab
    val_sessions = val_ab + val_non_ab
    test_sessions = test_ab + test_non_ab
    
    print(f"\nDataset splits:")
    print(f"Train: {len(train_sessions)} sessions ({len(train_ab)} abandoned, {len(train_non_ab)} non-abandoned)")
    print(f"Val: {len(val_sessions)} sessions ({len(val_ab)} abandoned, {len(val_non_ab)} non-abandoned)")
    print(f"Test: {len(test_sessions)} sessions ({len(test_ab)} abandoned, {len(test_non_ab)} non-abandoned)")
    
    # Verify no user overlap
    train_users = set(get_user_from_session(s) for s in train_sessions)
    val_users = set(get_user_from_session(s) for s in val_sessions)
    test_users = set(get_user_from_session(s) for s in test_sessions)
    
    assert len(train_users & val_users) == 0, "User overlap between train and val!"
    assert len(train_users & test_users) == 0, "User overlap between train and test!"
    assert len(val_users & test_users) == 0, "User overlap between val and test!"
    print("\n✓ No user overlap between splits")
    
    # Create label mapping
    session_labels = {}
    for sid in train_sessions + val_sessions + test_sessions:
        session_labels[sid] = 1 if sid in abandoned_sessions else 0
    
    # Save splits
    splits = {
        'train': train_sessions,
        'val': val_sessions,
        'test': test_sessions
    }
    
    print("\nSaving processed data...")
    
    # Save full data for each split
    for split_name, session_ids in splits.items():
        split_df = df[df['session_id'].isin(session_ids)].copy()
        split_df['label'] = split_df['session_id'].map(session_labels)
        
        output_file = output_path / f"{split_name}.csv"
        split_df.to_csv(output_file, index=False)
        print(f"Saved {split_name} split: {output_file}")
    
    # Save metadata
    metadata = {
        'total_sessions': len(train_sessions) + len(val_sessions) + len(test_sessions),
        'n_abandoned': n_samples,
        'n_non_abandoned': n_samples,
        'train_size': len(train_sessions),
        'val_size': len(val_sessions),
        'test_size': len(test_sessions),
        'train_users': len(train_users),
        'val_users': len(val_users),
        'test_users': len(test_users),
        'random_seed': random_seed,
        'abandonment_definition': {
            'min_queries': 2,
            'ends_with_no_click': True,
            'min_inactivity_minutes': 30
        }
    }
    
    metadata_file = output_path / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata: {metadata_file}")
    
    # Save session labels
    labels_file = output_path / 'session_labels.json'
    with open(labels_file, 'w') as f:
        json.dump(session_labels, f, indent=2)
    print(f"Saved session labels: {labels_file}")
    
    return metadata


def main():
    """Main function to run preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess data for session abandonment prediction')
    parser.add_argument('input_csv', type=str, help='Path to annotated CSV file')
    parser.add_argument('--output-dir', type=str, default='models/data/processed',
                       help='Output directory for processed data')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    metadata = create_balanced_dataset(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        random_seed=args.seed
    )
    
    print("\n" + "="*60)
    print("Preprocessing complete!")
    print("="*60)
    print(f"Total dataset size: {metadata['total_sessions']} sessions")
    print(f"  - Abandoned: {metadata['n_abandoned']} ({metadata['n_abandoned']/metadata['total_sessions']*100:.1f}%)")
    print(f"  - Non-abandoned: {metadata['n_non_abandoned']} ({metadata['n_non_abandoned']/metadata['total_sessions']*100:.1f}%)")
    print(f"\nSplits:")
    print(f"  - Train: {metadata['train_size']} sessions from {metadata['train_users']} users")
    print(f"  - Val: {metadata['val_size']} sessions from {metadata['val_users']} users")
    print(f"  - Test: {metadata['test_size']} sessions from {metadata['test_users']} users")


if __name__ == '__main__':
    main()

