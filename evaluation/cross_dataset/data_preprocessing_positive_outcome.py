#!/usr/bin/env python3
"""
Data preprocessing for Positive Outcome Prediction

TASK: Given context up to event t, predict whether the user's NEXT interaction
will be positive (target=1) or negative (target=0).

This is a dataset-aware task where the definition of "positive" and "negative"
outcomes varies by dataset, reflecting the natural engagement signals in each
domain.

DATASET-SPECIFIC TARGET DEFINITIONS:

AOL (action types: QUERY, SERP_VIEW, CLICK):
  - Positive (1): next event is CLICK (user found something worth clicking)
  - Negative (0): next event is QUERY (user reformulated without clicking)
  - Skip: next event is SERP_VIEW (intermediate, not a clear outcome)

StackOverflow (action types: COMMENT, POST_ANSWER, POST_QUESTION, EDIT_*, VOTE_*):
  - Positive (1): next event is POST_ANSWER (user produces a solution)
  - Negative (0): next event is COMMENT or POST_QUESTION (still seeking/discussing)
  - Skip: EDIT_* or VOTE_* events (editorial/meta, not engagement quality)

MovieLens (action types: RATE, BELIEF_ELICIT, BELIEF_PREDICT):
  - Positive (1): next RATE event has rating >= 4.0
  - Negative (0): next RATE event has rating <= 2.5
  - Skip: middle ratings (2.5 < rating < 4.0) and non-RATE targets
  - Filter out invalid ratings of -1.0

PRACTICAL UTILITY:
- Predict whether the user's next step signals engagement or frustration
- Enable real-time ranking and recommendation adjustments
- Route users toward more productive interaction paths

DESIGN:
- Input: Session prefix e_1...e_t (minimum 2 events of context)
- Target: 1 = positive next interaction, 0 = negative next interaction
- Balanced by downsampling the majority class
- Split by users (80/10/10) to prevent leakage
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json


def get_user_from_session(session_id: str) -> str:
    """Extract user ID from session ID. Handles AOL, SO, and ML formats."""
    if session_id.startswith('so_session_'):
        # SO format: so_session_N -- use hash to create synthetic users
        num = session_id.split('_')[-1]
        return f'so_user_{int(num) % 500}'
    elif session_id.startswith('ml_'):
        # ML format: ml_USERID_N -- extract middle segment as user
        parts = session_id.split('_')
        return parts[1] if len(parts) >= 3 else session_id
    else:
        # AOL format: USERID_SESSIONNUM
        return session_id.split('_')[0] if '_' in session_id else session_id


def create_aol_samples(df: pd.DataFrame) -> List[Dict]:
    """
    Create positive outcome samples for AOL dataset.

    For each event at position t (t >= 1, so at least 2 events of context),
    look at event at t+1:
      - Positive (1): next action_type is CLICK
      - Negative (0): next action_type is QUERY
      - Skip: next action_type is SERP_VIEW
    """
    samples = []

    for session_id, session_df in df.groupby('session_id'):
        session_df = session_df.sort_values('event_timestamp').reset_index(drop=True)
        events = session_df.to_dict('records')

        for t in range(1, len(events) - 1):
            next_action = events[t + 1]['action_type']

            if next_action == 'CLICK':
                target = 1
            elif next_action == 'QUERY':
                target = 0
            else:
                continue  # Skip SERP_VIEW

            prefix_events = events[:t + 1]

            sample = {
                'session_id': f"{session_id}_t{t}",
                'original_session_id': session_id,
                'events': prefix_events,
                'target': target,
                'next_action': next_action,
                'context_length': len(prefix_events)
            }
            samples.append(sample)

    return samples


def create_stackoverflow_samples(df: pd.DataFrame) -> List[Dict]:
    """
    Create positive outcome samples for StackOverflow dataset.

    For each event at position t (t >= 1, so at least 2 events of context),
    look at event at t+1:
      - Positive (1): next action is POST_ANSWER
      - Negative (0): next action is COMMENT or POST_QUESTION
      - Skip: EDIT_* or VOTE_* events
    """
    negative_actions = {'COMMENT', 'POST_QUESTION'}
    skip_prefixes = ('EDIT_', 'VOTE_')
    samples = []

    for session_id, session_df in df.groupby('session_id'):
        session_df = session_df.sort_values('event_timestamp').reset_index(drop=True)
        events = session_df.to_dict('records')

        for t in range(1, len(events) - 1):
            next_action = events[t + 1]['action_type']

            if next_action == 'POST_ANSWER':
                target = 1
            elif next_action in negative_actions:
                target = 0
            elif next_action.startswith(skip_prefixes):
                continue  # Skip editorial/meta actions
            else:
                continue

            prefix_events = events[:t + 1]

            sample = {
                'session_id': f"{session_id}_t{t}",
                'original_session_id': session_id,
                'events': prefix_events,
                'target': target,
                'next_action': next_action,
                'context_length': len(prefix_events)
            }
            samples.append(sample)

    return samples


def create_movielens_samples(df: pd.DataFrame) -> List[Dict]:
    """
    Create positive outcome samples for MovieLens dataset.

    For each event at position t (t >= 1, so at least 2 events of context),
    look at the next RATE event after t:
      - Parse the content JSON to extract the "rating" field
      - Positive (1): rating >= 4.0
      - Negative (0): rating <= 2.5
      - Skip: middle ratings (2.5 < rating < 4.0) and invalid ratings (-1.0)
      - Skip if no RATE event follows
    """
    samples = []

    for session_id, session_df in df.groupby('session_id'):
        session_df = session_df.sort_values('event_timestamp').reset_index(drop=True)
        events = session_df.to_dict('records')

        for t in range(1, len(events) - 1):
            # Find the next RATE event after position t
            next_rate_event = None
            for j in range(t + 1, len(events)):
                if events[j]['action_type'] == 'RATE':
                    next_rate_event = events[j]
                    break

            if next_rate_event is None:
                continue  # No RATE event follows

            # Parse rating from content
            try:
                content = next_rate_event.get('content', '{}')
                if isinstance(content, str):
                    content_data = json.loads(content)
                else:
                    content_data = content
                rating = float(content_data.get('rating', -1.0))
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

            # Filter out invalid ratings
            if rating == -1.0:
                continue

            # Classify by rating threshold
            if rating >= 4.0:
                target = 1
            elif rating <= 2.5:
                target = 0
            else:
                continue  # Skip middle ratings for cleaner signal

            prefix_events = events[:t + 1]

            sample = {
                'session_id': f"{session_id}_t{t}",
                'original_session_id': session_id,
                'events': prefix_events,
                'target': target,
                'next_action': 'RATE',
                'rating': rating,
                'context_length': len(prefix_events)
            }
            samples.append(sample)

    return samples


def analyze_cognitive_label_patterns(samples: List[Dict]) -> None:
    """Print analysis of cognitive label patterns vs positive outcome."""
    print("\n=== COGNITIVE LABEL PATTERNS vs POSITIVE OUTCOME ===")

    # Collect cognitive labels from the last event in each sample's context
    by_label = {}
    for s in samples:
        last_event = s['events'][-1]
        label = last_event.get('cognitive_label', 'UNKNOWN')
        if pd.isna(label) or label == '':
            label = 'UNKNOWN'
        if label not in by_label:
            by_label[label] = {'positive': 0, 'negative': 0}
        if s['target'] == 1:
            by_label[label]['positive'] += 1
        else:
            by_label[label]['negative'] += 1

    print("\nBy last context event's cognitive label:")
    for label in sorted(by_label.keys()):
        counts = by_label[label]
        total = counts['positive'] + counts['negative']
        pos_pct = 100 * counts['positive'] / total if total > 0 else 0
        print(f"  {label}: {pos_pct:.1f}% positive (n={total})")

    # Analyze by context length
    print("\nBy context length:")
    by_length = {}
    for s in samples:
        length = min(s['context_length'], 6)  # bucket 6+
        bucket = str(length) if length < 6 else "6+"
        if bucket not in by_length:
            by_length[bucket] = {'positive': 0, 'negative': 0}
        if s['target'] == 1:
            by_length[bucket]['positive'] += 1
        else:
            by_length[bucket]['negative'] += 1

    for bucket in sorted(by_length.keys()):
        counts = by_length[bucket]
        total = counts['positive'] + counts['negative']
        pos_pct = 100 * counts['positive'] / total if total > 0 else 0
        print(f"  {bucket} events: {pos_pct:.1f}% positive (n={total})")


def balance_samples(samples: List[Dict], random_seed: int = 42) -> List[Dict]:
    """Balance positive vs negative samples by downsampling majority class."""
    np.random.seed(random_seed)

    positive = [s for s in samples if s['target'] == 1]
    negative = [s for s in samples if s['target'] == 0]

    print(f"  Before: {len(positive)} positive, {len(negative)} negative")

    min_count = min(len(positive), len(negative))

    if min_count < 10:
        print("  WARNING: Too few samples to balance effectively")
        if min_count == 0:
            return samples

    np.random.shuffle(positive)
    np.random.shuffle(negative)

    balanced = positive[:min_count] + negative[:min_count]
    np.random.shuffle(balanced)

    print(f"  After: {min_count} each, {len(balanced)} total")
    return balanced


def samples_to_dataframe(samples: List[Dict]) -> pd.DataFrame:
    """Convert samples to DataFrame format."""
    rows = []

    for sample in samples:
        for event in sample['events']:
            row = event.copy()
            row['session_id'] = sample['session_id']
            row['label'] = sample['target']
            rows.append(row)

    return pd.DataFrame(rows)


def create_dataset(
    input_csv: str,
    dataset: str,
    output_dir: str = "data/processed_positive_outcome",
    random_seed: int = 42
) -> Dict:
    """Create balanced dataset for positive outcome prediction."""
    np.random.seed(random_seed)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)

    print(f"Dataset: {dataset}")
    print(f"Total events: {len(df)}")
    print(f"Total sessions: {df['session_id'].nunique()}")

    # Create samples based on dataset type
    print(f"\nCreating positive outcome prediction samples for {dataset}...")

    if dataset == 'aol':
        all_samples = create_aol_samples(df)
    elif dataset == 'stackoverflow':
        all_samples = create_stackoverflow_samples(df)
    elif dataset == 'movielens':
        all_samples = create_movielens_samples(df)
    else:
        raise ValueError(f"Unknown dataset: {dataset}")

    print(f"Total samples: {len(all_samples)}")

    if len(all_samples) == 0:
        print("ERROR: No valid samples created!")
        return {'train_samples': 0, 'val_samples': 0, 'test_samples': 0}

    # Distribution
    n_positive = sum(1 for s in all_samples if s['target'] == 1)
    n_negative = len(all_samples) - n_positive
    print(f"Distribution: {n_positive} positive ({100*n_positive/len(all_samples):.1f}%), "
          f"{n_negative} negative ({100*n_negative/len(all_samples):.1f}%)")

    # Analyze cognitive label patterns
    analyze_cognitive_label_patterns(all_samples)

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

    # Assign samples to splits
    train_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in train_users]
    val_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in val_users]
    test_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in test_users]

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
            pd.DataFrame(columns=['session_id', 'label']).to_csv(output_path / f"{split_name}.csv", index=False)
            print(f"WARNING: {split_name} is empty")
            continue

        split_df = samples_to_dataframe(samples)
        split_df.to_csv(output_path / f"{split_name}.csv", index=False)

        n_p = sum(1 for s in samples if s['target'] == 1)
        print(f"Saved {split_name}: {len(split_df)} rows, {len(samples)} samples "
              f"({n_p} positive, {len(samples)-n_p} negative)")

    # Build target definition for metadata
    target_defs = {
        'aol': {
            'positive': 'next action_type is CLICK (user found something worth clicking)',
            'negative': 'next action_type is QUERY (user reformulated without clicking)',
            'skipped': 'SERP_VIEW (intermediate, not a clear outcome)'
        },
        'stackoverflow': {
            'positive': 'next action is POST_ANSWER (user produces a solution)',
            'negative': 'next action is COMMENT or POST_QUESTION (still seeking/discussing)',
            'skipped': 'EDIT_* or VOTE_* (editorial/meta, not engagement quality)'
        },
        'movielens': {
            'positive': 'next RATE event has rating >= 4.0',
            'negative': 'next RATE event has rating <= 2.5',
            'skipped': 'middle ratings (2.5 < rating < 4.0), non-RATE events, invalid ratings (-1.0)'
        }
    }

    metadata = {
        'task': 'positive_outcome_prediction',
        'dataset': dataset,
        'description': f'Predict whether next interaction is positive (1) or negative (0) for {dataset} dataset',
        'target_definition': target_defs[dataset],
        'min_context_events': 2,
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
    parser = argparse.ArgumentParser(
        description='Preprocess data for positive outcome prediction'
    )
    parser.add_argument('input_csv', type=str, help='Path to annotated CSV file')
    parser.add_argument('--dataset', type=str, required=True,
                        choices=['aol', 'stackoverflow', 'movielens'],
                        help='Dataset type (determines target definition)')
    parser.add_argument('--output-dir', type=str, default='data/processed_positive_outcome',
                        help='Output directory for processed data')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    args = parser.parse_args()

    metadata = create_dataset(args.input_csv, args.dataset, args.output_dir, args.seed)
    print(f"\nDone! Train: {metadata['train_samples']}, Val: {metadata['val_samples']}, Test: {metadata['test_samples']}")


if __name__ == '__main__':
    main()
