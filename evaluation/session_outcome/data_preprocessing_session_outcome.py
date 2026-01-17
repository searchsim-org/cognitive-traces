#!/usr/bin/env python3
"""
Data preprocessing for Session Outcome Prediction

TASK: Given the first half of a session, predict if the session will end
in a SUCCESS state (ApproachingSource, ForagingSuccess) or FAILURE state
(LeavingPatch, PoorScent with session abandonment).

This is a session-level prediction task that tests whether cognitive signals
in early events can forecast overall session outcome.

RATIONALE:
- Early intervention in search sessions can improve user experience
- If we can predict session failure early, systems can provide assistance
- This task has practical utility for search systems
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json


SUCCESS_LABELS = {'ApproachingSource', 'ForagingSuccess', 'DietEnrichment'}
FAILURE_LABELS = {'PoorScent', 'LeavingPatch'}


def get_user_from_session(session_id: str) -> str:
    """Extract user ID from session ID."""
    return session_id.split('_')[0] if '_' in session_id else session_id


def get_session_outcome(session_df: pd.DataFrame) -> int:
    """
    Determine session outcome.

    SUCCESS (1): Session's final event is a success state OR session contains
                 ApproachingSource/ForagingSuccess anywhere
    FAILURE (0): Session ends in failure state without any success markers
    """
    labels = session_df['cognitive_label'].values

    # Check if session ever reached success
    has_success = any(label in SUCCESS_LABELS for label in labels)

    # Check final state
    final_label = labels[-1]
    ends_in_failure = final_label in FAILURE_LABELS

    # Success if reached success state at any point
    if has_success:
        return 1
    # Failure if ends in failure without success
    elif ends_in_failure:
        return 0
    else:
        return 1  # Default to success if unclear


def create_early_prediction_samples(
    df: pd.DataFrame,
    prefix_ratio: float = 0.5,  # Use first 50% of session
    min_events: int = 4,  # Minimum session length
    random_seed: int = 42
) -> List[Dict]:
    """
    Create samples for session outcome prediction from early events.

    For each session:
    - Input: First prefix_ratio of events
    - Target: Session outcome (success=1, failure=0)
    """
    np.random.seed(random_seed)
    samples = []

    for session_id, session_df in df.groupby('session_id'):
        session_df = session_df.sort_values('event_timestamp')
        events = session_df.to_dict('records')

        # Skip short sessions
        if len(events) < min_events:
            continue

        # Determine session outcome
        outcome = get_session_outcome(session_df)

        # Take first half of events
        n_prefix = max(2, int(len(events) * prefix_ratio))
        prefix_events = events[:n_prefix]

        sample = {
            'session_id': session_id,
            'events': prefix_events,
            'target': outcome,
            'full_length': len(events),
            'prefix_length': n_prefix,
            'original_session_id': session_id
        }
        samples.append(sample)

    return samples


def balance_samples(samples: List[Dict], random_seed: int = 42) -> List[Dict]:
    """Balance success vs failure samples."""
    np.random.seed(random_seed)

    success = [s for s in samples if s['target'] == 1]
    failure = [s for s in samples if s['target'] == 0]

    print(f"  Before: {len(success)} success, {len(failure)} failure")

    min_count = min(len(success), len(failure))

    if min_count == 0:
        print("  WARNING: Cannot balance")
        return samples

    np.random.shuffle(success)
    np.random.shuffle(failure)

    balanced = success[:min_count] + failure[:min_count]
    np.random.shuffle(balanced)

    print(f"  After: {min_count} each, {len(balanced)} total")
    return balanced


def samples_to_dataframe(samples: List[Dict]) -> pd.DataFrame:
    """Convert samples to DataFrame format."""
    rows = []

    for sample in samples:
        prefix_sid = f"{sample['original_session_id']}_outcome"

        for event in sample['events']:
            row = event.copy()
            row['session_id'] = prefix_sid
            row['label'] = sample['target']
            rows.append(row)

    return pd.DataFrame(rows)


def create_dataset(
    input_csv: str,
    output_dir: str = "data/processed_session_outcome",
    prefix_ratio: float = 0.5,
    random_seed: int = 42
) -> Dict:
    """Create balanced dataset for session outcome prediction."""
    np.random.seed(random_seed)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)

    print(f"Total events: {len(df)}")
    print(f"Total sessions: {df['session_id'].nunique()}")

    # Create samples
    print(f"\nCreating session outcome samples (first {int(prefix_ratio*100)}% of events)...")
    all_samples = create_early_prediction_samples(df, prefix_ratio, random_seed=random_seed)
    print(f"Total samples (sessions with 4+ events): {len(all_samples)}")

    # Distribution
    n_success = sum(1 for s in all_samples if s['target'] == 1)
    n_failure = len(all_samples) - n_success
    print(f"Distribution: {n_success} success ({100*n_success/len(all_samples):.1f}%), "
          f"{n_failure} failure ({100*n_failure/len(all_samples):.1f}%)")

    # Split by users
    sample_users = list(set(get_user_from_session(s['original_session_id']) for s in all_samples))
    np.random.shuffle(sample_users)

    n_users = len(sample_users)
    n_train = int(n_users * 0.8)
    n_val = int(n_users * 0.1)

    train_users = set(sample_users[:n_train])
    val_users = set(sample_users[n_train:n_train + n_val])
    test_users = set(sample_users[n_train + n_val:])

    print(f"\nUser split: {len(train_users)} train, {len(val_users)} val, {len(test_users)} test")

    # Assign and balance
    train_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in train_users]
    val_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in val_users]
    test_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in test_users]

    print(f"\nBefore balancing:")
    print(f"  Train: {len(train_samples)}")
    print(f"  Val: {len(val_samples)}")
    print(f"  Test: {len(test_samples)}")

    print("\nBalancing train:")
    train_samples = balance_samples(train_samples, random_seed)
    print("Balancing val:")
    val_samples = balance_samples(val_samples, random_seed + 1)
    print("Balancing test:")
    test_samples = balance_samples(test_samples, random_seed + 2)

    # Save
    splits = {'train': train_samples, 'val': val_samples, 'test': test_samples}

    for split_name, samples in splits.items():
        if len(samples) == 0:
            pd.DataFrame(columns=['session_id', 'label']).to_csv(output_path / f"{split_name}.csv", index=False)
            continue

        split_df = samples_to_dataframe(samples)
        split_df.to_csv(output_path / f"{split_name}.csv", index=False)

        n_s = sum(1 for s in samples if s['target'] == 1)
        print(f"Saved {split_name}: {len(split_df)} rows, {len(samples)} samples ({n_s} success, {len(samples)-n_s} failure)")

    metadata = {
        'task': 'session_outcome_prediction',
        'description': 'Predict session success/failure from first 50% of events',
        'prefix_ratio': prefix_ratio,
        'success_labels': list(SUCCESS_LABELS),
        'failure_labels': list(FAILURE_LABELS),
        'train_samples': len(train_samples),
        'val_samples': len(val_samples),
        'test_samples': len(test_samples),
        'random_seed': random_seed
    }

    with open(output_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv', type=str)
    parser.add_argument('--output-dir', type=str, default='models/data/processed_session_outcome')
    parser.add_argument('--prefix-ratio', type=float, default=0.5)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    metadata = create_dataset(args.input_csv, args.output_dir, args.prefix_ratio, args.seed)
    print(f"\nDone! Train: {metadata['train_samples']}, Val: {metadata['val_samples']}, Test: {metadata['test_samples']}")


if __name__ == '__main__':
    main()
