#!/usr/bin/env python3
"""
Data preprocessing for Session Success from Early Context

TASK: Given only the first N events of a session, predict whether the session
will end successfully. This is a fixed-window early prediction task that tests
whether initial behavioral and cognitive signals can forecast the full session
outcome.

MOTIVATION: Predicting session outcomes from early signals enables proactive
intervention in interactive systems. If a system can detect likely failure within
the first few events, it can take corrective action -- search result re-ranking,
recommendation adjustment, engagement optimization, or proactive assistance --
before the user abandons or has a poor experience. This has direct practical
value for search engines, recommendation systems, and Q&A platforms.

DESIGN:
- Input: First 3 events of each session (fixed early context window)
- Target: Defined by the FULL session outcome (not early events)
- Filter: Sessions must have >= 6 events (3 for input, 3+ for meaningful
  future context that separates success from failure)

DATASET-SPECIFIC SUCCESS DEFINITIONS:

  AOL (action types: QUERY, SERP_VIEW, CLICK):
    Success (1): Session has exactly 3 queries (minimum; efficient one-shot search)
    Failure (0): Session has 4+ queries (needed reformulation; struggled)

  StackOverflow (action types: COMMENT, POST_ANSWER, POST_QUESTION, EDIT_*):
    Success (1): Session contains at least one POST_ANSWER event
    Failure (0): Session has NO POST_ANSWER events (consumption-only)

  MovieLens (action types: RATE, BELIEF_ELICIT, BELIEF_PREDICT):
    Success (1): Session contains at least one RATE event with rating >= 4.0
    Failure (0): ALL RATE events have rating < 4.0 (no strong positive)
    Note: Ratings of -1.0 are ignored (sentinel/missing values)

The fixed 3-event window is deliberately small to test whether genuinely early
signals have predictive power. The minimum session length of 6 ensures that the
outcome depends on substantial future behavior beyond what the model observes.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json
from collections import defaultdict


# ---------------------------------------------------------------------------
# User extraction
# ---------------------------------------------------------------------------

def get_user_from_session(session_id: str) -> str:
    """Extract user ID from session ID. Handles AOL, SO, and ML formats."""
    if session_id.startswith('so_session_'):
        # SO format: so_session_N — use hash to create synthetic users
        num = session_id.split('_')[-1]
        return f'so_user_{int(num) % 500}'
    elif session_id.startswith('ml_'):
        # ML format: ml_USERID_N — extract middle segment as user
        parts = session_id.split('_')
        return parts[1] if len(parts) >= 3 else session_id
    else:
        # AOL format: USERID_SESSIONNUM
        return session_id.split('_')[0] if '_' in session_id else session_id


# ---------------------------------------------------------------------------
# Dataset-specific success definitions
# ---------------------------------------------------------------------------

def _parse_rating(content: str) -> float:
    """Parse rating from MovieLens content JSON. Returns -1.0 on failure."""
    try:
        data = json.loads(content)
        return float(data.get('rating', -1.0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return -1.0


def get_session_success_aol(session_df: pd.DataFrame) -> int:
    """AOL: Success if session has exactly 3 queries (efficient, no reformulation needed).
    Failure if 4+ queries (user struggled, needed multiple reformulations).
    All AOL sessions end with CLICK, so last-event-based targets are degenerate.
    """
    n_queries = (session_df['action_type'] == 'QUERY').sum()
    return 1 if n_queries <= 3 else 0


def get_session_success_stackoverflow(session_df: pd.DataFrame) -> int:
    """StackOverflow: Success if session contains at least one POST_ANSWER."""
    has_answer = (session_df['action_type'] == 'POST_ANSWER').any()
    return 1 if has_answer else 0


def get_session_success_movielens(session_df: pd.DataFrame) -> int:
    """MovieLens: Success if any RATE event has rating >= 4.0.

    Ratings of -1.0 are ignored as sentinel/missing values.
    """
    rate_events = session_df[session_df['action_type'] == 'RATE']
    if len(rate_events) == 0:
        return 0

    for _, row in rate_events.iterrows():
        rating = _parse_rating(row['content'])
        if rating < 0:
            continue  # skip sentinel values
        if rating >= 4.0:
            return 1

    return 0


# Dispatcher
SUCCESS_FUNCTIONS = {
    'aol': get_session_success_aol,
    'stackoverflow': get_session_success_stackoverflow,
    'movielens': get_session_success_movielens,
}


# ---------------------------------------------------------------------------
# Sample creation
# ---------------------------------------------------------------------------

def create_early_context_samples(
    df: pd.DataFrame,
    dataset: str,
    n_early: int = 3,
    min_events: int = 6,
) -> List[Dict]:
    """
    Create samples for session success prediction from early context.

    For each session with >= min_events:
    - Compute target from the FULL session (dataset-specific definition)
    - Take only the first n_early events as the input sample
    - session_id is tagged with "_early" suffix
    """
    success_fn = SUCCESS_FUNCTIONS[dataset]
    samples = []

    for session_id, session_df in df.groupby('session_id'):
        session_df = session_df.sort_values('event_timestamp').reset_index(drop=True)
        events = session_df.to_dict('records')

        # Require sufficient length for meaningful future context
        if len(events) < min_events:
            continue

        # Target from full session
        target = success_fn(session_df)

        # Input from early events only
        early_events = events[:n_early]

        sample = {
            'session_id': f"{session_id}_early",
            'original_session_id': session_id,
            'events': early_events,
            'target': target,
            'full_length': len(events),
            'early_length': n_early,
        }
        samples.append(sample)

    return samples


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_early_cognitive_patterns(samples: List[Dict]) -> None:
    """Print cognitive label patterns in early events vs session success."""
    print("\n=== COGNITIVE LABEL PATTERNS IN EARLY EVENTS VS SUCCESS ===")

    # Collect cognitive labels from early events
    label_outcomes = defaultdict(lambda: {'success': 0, 'failure': 0})

    for s in samples:
        for event in s['events']:
            label = event.get('cognitive_label', 'unknown')
            if s['target'] == 1:
                label_outcomes[label]['success'] += 1
            else:
                label_outcomes[label]['failure'] += 1

    for label in sorted(label_outcomes.keys()):
        counts = label_outcomes[label]
        total = counts['success'] + counts['failure']
        success_pct = 100 * counts['success'] / total if total > 0 else 0
        print(f"  {label}: {success_pct:.1f}% in successful sessions "
              f"(n={total}, success={counts['success']}, failure={counts['failure']})")


def analyze_early_action_patterns(samples: List[Dict]) -> None:
    """Print action type patterns in early events vs session success."""
    print("\n=== ACTION TYPE PATTERNS IN EARLY EVENTS VS SUCCESS ===")

    action_outcomes = defaultdict(lambda: {'success': 0, 'failure': 0})

    for s in samples:
        for event in s['events']:
            action = event.get('action_type', 'unknown')
            if s['target'] == 1:
                action_outcomes[action]['success'] += 1
            else:
                action_outcomes[action]['failure'] += 1

    for action in sorted(action_outcomes.keys()):
        counts = action_outcomes[action]
        total = counts['success'] + counts['failure']
        success_pct = 100 * counts['success'] / total if total > 0 else 0
        print(f"  {action}: {success_pct:.1f}% in successful sessions "
              f"(n={total}, success={counts['success']}, failure={counts['failure']})")


# ---------------------------------------------------------------------------
# Balancing
# ---------------------------------------------------------------------------

def balance_samples(samples: List[Dict], random_seed: int = 42) -> List[Dict]:
    """Balance success vs failure samples by downsampling majority class."""
    np.random.seed(random_seed)

    success = [s for s in samples if s['target'] == 1]
    failure = [s for s in samples if s['target'] == 0]

    print(f"  Before: {len(success)} success, {len(failure)} failure")

    min_count = min(len(success), len(failure))

    if min_count == 0:
        print("  WARNING: Cannot balance - one class is empty")
        return samples

    np.random.shuffle(success)
    np.random.shuffle(failure)

    balanced = success[:min_count] + failure[:min_count]
    np.random.shuffle(balanced)

    print(f"  After: {min_count} each, {len(balanced)} total")
    return balanced


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def samples_to_dataframe(samples: List[Dict]) -> pd.DataFrame:
    """Convert samples to DataFrame format where each row is an event."""
    rows = []

    for sample in samples:
        for event in sample['events']:
            row = event.copy()
            row['session_id'] = sample['session_id']
            row['label'] = sample['target']
            rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def create_dataset(
    input_csv: str,
    dataset: str,
    output_dir: str = "data/processed_session_success_early",
    n_early: int = 3,
    min_events: int = 6,
    random_seed: int = 42,
) -> Dict:
    """Create balanced dataset for session success prediction from early context."""
    np.random.seed(random_seed)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)

    print(f"Dataset: {dataset}")
    print(f"Total events: {len(df)}")
    print(f"Total sessions: {df['session_id'].nunique()}")

    # Create samples
    print(f"\nCreating early context samples (first {n_early} events, "
          f"sessions with {min_events}+ events)...")
    all_samples = create_early_context_samples(df, dataset, n_early, min_events)
    print(f"Total samples (qualifying sessions): {len(all_samples)}")

    if len(all_samples) == 0:
        print("ERROR: No valid samples created!")
        return {'train_samples': 0, 'val_samples': 0, 'test_samples': 0}

    # Class distribution
    n_success = sum(1 for s in all_samples if s['target'] == 1)
    n_failure = len(all_samples) - n_success
    print(f"\nClass distribution:")
    print(f"  Success: {n_success} ({100 * n_success / len(all_samples):.1f}%)")
    print(f"  Failure: {n_failure} ({100 * n_failure / len(all_samples):.1f}%)")

    # Analyze patterns
    analyze_early_cognitive_patterns(all_samples)
    analyze_early_action_patterns(all_samples)

    # Split by users (80/10/10)
    sample_users = list(set(
        get_user_from_session(s['original_session_id']) for s in all_samples
    ))
    np.random.shuffle(sample_users)

    n_users = len(sample_users)
    n_train = int(n_users * 0.8)
    n_val = int(n_users * 0.1)

    train_users = set(sample_users[:n_train])
    val_users = set(sample_users[n_train:n_train + n_val])
    test_users = set(sample_users[n_train + n_val:])

    print(f"\nUser split: {len(train_users)} train, {len(val_users)} val, "
          f"{len(test_users)} test")

    # Assign samples to splits
    train_samples = [
        s for s in all_samples
        if get_user_from_session(s['original_session_id']) in train_users
    ]
    val_samples = [
        s for s in all_samples
        if get_user_from_session(s['original_session_id']) in val_users
    ]
    test_samples = [
        s for s in all_samples
        if get_user_from_session(s['original_session_id']) in test_users
    ]

    print(f"\nBefore balancing:")
    print(f"  Train: {len(train_samples)}")
    print(f"  Val: {len(val_samples)}")
    print(f"  Test: {len(test_samples)}")

    # Balance each split
    print("\nBalancing train:")
    train_samples = balance_samples(train_samples, random_seed)
    print("Balancing val:")
    val_samples = balance_samples(val_samples, random_seed + 1)
    print("Balancing test:")
    test_samples = balance_samples(test_samples, random_seed + 2)

    # Save splits
    splits = {'train': train_samples, 'val': val_samples, 'test': test_samples}

    for split_name, samples in splits.items():
        if len(samples) == 0:
            print(f"WARNING: {split_name} split is empty!")
            pd.DataFrame(columns=['session_id', 'label']).to_csv(
                output_path / f"{split_name}.csv", index=False
            )
            continue

        split_df = samples_to_dataframe(samples)
        split_df.to_csv(output_path / f"{split_name}.csv", index=False)

        n_s = sum(1 for s in samples if s['target'] == 1)
        print(f"Saved {split_name}: {len(split_df)} rows, {len(samples)} samples "
              f"({n_s} success, {len(samples) - n_s} failure)")

    # Save metadata
    metadata = {
        'task': 'session_success_early_prediction',
        'dataset': dataset,
        'description': (
            f'Predict session success from first {n_early} events. '
            f'Sessions require {min_events}+ total events.'
        ),
        'target_definition': {
            'aol': 'Success = session has <= 3 queries (efficient); Failure = 4+ queries (reformulation needed)',
            'stackoverflow': 'Success = session contains POST_ANSWER; Failure = no POST_ANSWER',
            'movielens': 'Success = any RATE with rating >= 4.0; Failure = all ratings < 4.0',
        }[dataset],
        'input_window': n_early,
        'min_session_length': min_events,
        'train_samples': len(train_samples),
        'val_samples': len(val_samples),
        'test_samples': len(test_samples),
        'train_users': len(train_users),
        'val_users': len(val_users),
        'test_users': len(test_users),
        'random_seed': random_seed,
    }

    with open(output_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"\nSaved metadata to {output_path / 'metadata.json'}")

    return metadata


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Preprocess data for Session Success from Early Context prediction'
    )
    parser.add_argument('input_csv', type=str,
                        help='Path to annotated CSV file')
    parser.add_argument('--dataset', type=str, required=True,
                        choices=['aol', 'stackoverflow', 'movielens'],
                        help='Dataset type (determines success definition)')
    parser.add_argument('--output-dir', type=str,
                        default='models/data/processed_session_success_early',
                        help='Output directory for processed data')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    args = parser.parse_args()

    metadata = create_dataset(
        input_csv=args.input_csv,
        dataset=args.dataset,
        output_dir=args.output_dir,
        random_seed=args.seed,
    )

    print("\n" + "=" * 60)
    print("Preprocessing complete!")
    print("=" * 60)
    print(f"Dataset: {args.dataset}")
    print(f"Train: {metadata['train_samples']} samples")
    print(f"Val:   {metadata['val_samples']} samples")
    print(f"Test:  {metadata['test_samples']} samples")


if __name__ == '__main__':
    main()
