#!/usr/bin/env python3
"""
Data preprocessing for Session Continuation Prediction

TASK: Given a session prefix up to event t (with at least 2 prior events of
context), predict whether the session will continue (target=1) or end
(target=0) after that event.

PRACTICAL UTILITY:
- If CONTINUE predicted: Pre-fetch resources, keep session state warm,
  prepare suggestions for next actions
- If END predicted: Release resources, trigger post-session analytics,
  prompt satisfaction surveys
- Enables proactive session management and infrastructure optimization

DESIGN:
- Input: Full session prefix [0..t] where t >= 2 (minimum 2 events of context)
- Target: 1 = session continues (more events follow event t)
           0 = session ends (event t is the last event)
- Every event at position t >= 2 produces exactly one sample
- The last event in every session always has target=0
- All non-final events (with t >= 2) have target=1

This task is purely behavioral and dataset-agnostic: the target is determined
entirely by whether additional events follow the current position, with no
dependence on action types or domain-specific semantics. It works identically
across AOL (web search), StackOverflow (Q&A), and MovieLens (movie ratings).

COGNITIVE RATIONALE:
- Sessions ending in struggle states (PoorScent, LeavingPatch) may reflect
  abandonment rather than satisfaction, providing signal beyond raw position
- ForagingSuccess or ApproachingSource at event t may indicate the user has
  found what they need, predicting session end
- A behavioral-only model sees only sequence length and action patterns; the
  cognitive model can distinguish "satisfied ending" from "frustrated ending"

DATASET-SPECIFIC USER EXTRACTION:
- AOL: session_id format "USERID_SESSIONNUM" -> user = first segment
- StackOverflow: session_id format "so_session_N" -> synthetic user via hash
- MovieLens: session_id format "ml_USERID_N" -> user = middle segment
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json


def get_user_from_session(session_id: str, dataset: str) -> str:
    """Extract user ID from session ID. Handles AOL, SO, and ML formats.

    Args:
        session_id: The raw session identifier string.
        dataset: One of 'aol', 'stackoverflow', 'movielens'.

    Returns:
        A string representing the user who owns this session.
    """
    if dataset == 'stackoverflow':
        # SO format: so_session_N -- use modular hash to create synthetic users
        num = session_id.split('_')[-1]
        return f'so_user_{int(num) % 500}'
    elif dataset == 'movielens':
        # ML format: ml_USERID_N -- extract middle segment as user
        parts = session_id.split('_')
        return parts[1] if len(parts) >= 3 else session_id
    else:
        # AOL format: USERID_SESSIONNUM
        return session_id.split('_')[0] if '_' in session_id else session_id


def create_continuation_samples(df: pd.DataFrame) -> List[Dict]:
    """
    Create samples for session continuation prediction.

    For each event at position t (t >= 2, requiring at least 2 prior events of
    context), create a sample whose target indicates whether the session
    continues beyond t.

    - target=1 if t < len(session)-1  (more events follow)
    - target=0 if t == len(session)-1 (session ends here)

    Args:
        df: DataFrame with columns session_id, event_id, event_timestamp,
            action_type, content, cognitive_label.

    Returns:
        List of sample dicts, each containing the event prefix, target, and
        metadata.
    """
    samples = []

    for session_id, session_df in df.groupby('session_id'):
        session_df = session_df.sort_values('event_timestamp').reset_index(drop=True)
        events = session_df.to_dict('records')
        n_events = len(events)

        # Need at least 3 events total so that position t=2 has 2 prior events
        if n_events < 3:
            continue

        for t in range(2, n_events):
            # Determine whether the session continues after position t
            is_last = (t == n_events - 1)
            target = 0 if is_last else 1

            # Build event prefix: all events from 0 through t (inclusive)
            prefix_events = events[:t + 1]

            # Cognitive label of the current (decision-point) event
            current_label = events[t].get('cognitive_label', None)

            sample = {
                'session_id': f"{session_id}_evt{t}",
                'original_session_id': session_id,
                'events': prefix_events,
                'target': target,
                'current_cognitive_label': current_label,
                'prefix_length': len(prefix_events),
            }
            samples.append(sample)

    return samples


def analyze_patterns(samples: List[Dict]) -> None:
    """Print cognitive-label distribution for continue vs end events."""
    print("\n=== COGNITIVE LABEL -> CONTINUATION PATTERNS ===")

    by_label: Dict[str, Dict[str, int]] = {}
    for s in samples:
        label = s['current_cognitive_label']
        if label is None or (isinstance(label, float) and np.isnan(label)):
            label = '<MISSING>'
        if label not in by_label:
            by_label[label] = {'continue': 0, 'end': 0}

        if s['target'] == 1:
            by_label[label]['continue'] += 1
        else:
            by_label[label]['end'] += 1

    for label, counts in sorted(by_label.items()):
        total = counts['continue'] + counts['end']
        cont_pct = 100 * counts['continue'] / total if total > 0 else 0
        end_pct = 100 * counts['end'] / total if total > 0 else 0
        print(f"  {label}: CONTINUE={cont_pct:.1f}%, END={end_pct:.1f}% (n={total})")


def balance_samples(samples: List[Dict], random_seed: int = 42) -> List[Dict]:
    """Downsample the majority class to match the minority class size."""
    np.random.seed(random_seed)

    continues = [s for s in samples if s['target'] == 1]
    ends = [s for s in samples if s['target'] == 0]

    print(f"  Before: {len(continues)} continue, {len(ends)} end")

    min_count = min(len(continues), len(ends))

    if min_count < 10:
        print("  WARNING: Too few samples for meaningful balancing")
        if min_count == 0:
            return samples

    np.random.shuffle(continues)
    np.random.shuffle(ends)

    balanced = continues[:min_count] + ends[:min_count]
    np.random.shuffle(balanced)

    print(f"  After: {min_count} each, {len(balanced)} total")
    return balanced


def samples_to_dataframe(samples: List[Dict]) -> pd.DataFrame:
    """Convert sample list to a DataFrame compatible with dataset.py.

    Each row represents one event within a sample.  All events in a sample
    share the same session_id (the sample-level ID) and label (the target).

    Columns: session_id, event_id, event_timestamp, action_type, content,
             cognitive_label, label
    """
    rows = []

    for sample in samples:
        for event in sample['events']:
            row = {
                'session_id': sample['session_id'],
                'event_id': event.get('event_id', ''),
                'event_timestamp': event.get('event_timestamp', ''),
                'action_type': event.get('action_type', ''),
                'content': event.get('content', ''),
                'cognitive_label': event.get('cognitive_label', ''),
                'label': sample['target'],
            }
            rows.append(row)

    return pd.DataFrame(rows)


def create_dataset(
    input_csv: str,
    dataset: str,
    output_dir: str = "data/processed_session_continuation",
    random_seed: int = 42,
) -> Dict:
    """Create a balanced train/val/test dataset for session continuation prediction.

    Args:
        input_csv: Path to the annotated CSV with session events.
        dataset: Dataset identifier ('aol', 'stackoverflow', 'movielens').
        output_dir: Directory to write train.csv, val.csv, test.csv, metadata.json.
        random_seed: Random seed for reproducibility.

    Returns:
        Metadata dict summarising the created splits.
    """
    np.random.seed(random_seed)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)

    print(f"Total events: {len(df)}")
    print(f"Total sessions: {df['session_id'].nunique()}")

    # Create samples
    print("\nCreating session continuation samples...")
    all_samples = create_continuation_samples(df)
    print(f"Total samples: {len(all_samples)}")

    if len(all_samples) == 0:
        print("ERROR: No samples created. Check that sessions have >= 3 events.")
        metadata = {
            'task': 'session_continuation',
            'train_samples': 0, 'val_samples': 0, 'test_samples': 0,
            'random_seed': random_seed,
        }
        with open(output_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        return metadata

    # Distribution
    n_cont = sum(1 for s in all_samples if s['target'] == 1)
    n_end = len(all_samples) - n_cont
    print(f"Distribution: {n_cont} continue ({100*n_cont/len(all_samples):.1f}%), "
          f"{n_end} end ({100*n_end/len(all_samples):.1f}%)")

    # Analyze cognitive patterns
    analyze_patterns(all_samples)

    # ---- User-based train/val/test split ----
    sample_users = list(set(
        get_user_from_session(s['original_session_id'], dataset) for s in all_samples
    ))
    np.random.shuffle(sample_users)

    n_users = len(sample_users)
    n_train = int(n_users * 0.8)
    n_val = int(n_users * 0.1)

    train_users = set(sample_users[:n_train])
    val_users = set(sample_users[n_train:n_train + n_val])
    test_users = set(sample_users[n_train + n_val:])

    print(f"\nUser split: {len(train_users)} train, {len(val_users)} val, {len(test_users)} test")

    # Assign samples to splits
    train_samples = [s for s in all_samples
                     if get_user_from_session(s['original_session_id'], dataset) in train_users]
    val_samples = [s for s in all_samples
                   if get_user_from_session(s['original_session_id'], dataset) in val_users]
    test_samples = [s for s in all_samples
                    if get_user_from_session(s['original_session_id'], dataset) in test_users]

    print(f"\nBefore balancing:")
    print(f"  Train: {len(train_samples)}")
    print(f"  Val: {len(val_samples)}")
    print(f"  Test: {len(test_samples)}")

    # Balance each split independently
    print("\nBalancing train:")
    train_samples = balance_samples(train_samples, random_seed)
    print("Balancing val:")
    val_samples = balance_samples(val_samples, random_seed + 1)
    print("Balancing test:")
    test_samples = balance_samples(test_samples, random_seed + 2)

    # ---- Save splits ----
    splits = {'train': train_samples, 'val': val_samples, 'test': test_samples}

    for split_name, samples in splits.items():
        if len(samples) == 0:
            pd.DataFrame(
                columns=['session_id', 'event_id', 'event_timestamp',
                         'action_type', 'content', 'cognitive_label', 'label']
            ).to_csv(output_path / f"{split_name}.csv", index=False)
            continue

        split_df = samples_to_dataframe(samples)
        split_df.to_csv(output_path / f"{split_name}.csv", index=False)

        n_c = sum(1 for s in samples if s['target'] == 1)
        print(f"Saved {split_name}: {len(split_df)} rows, {len(samples)} samples "
              f"({n_c} continue, {len(samples)-n_c} end)")

    metadata = {
        'task': 'session_continuation',
        'description': 'At event t (t>=2), predict if session continues (1) or ends (0)',
        'dataset': dataset,
        'train_samples': len(train_samples),
        'val_samples': len(val_samples),
        'test_samples': len(test_samples),
        'random_seed': random_seed,
    }

    with open(output_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Preprocess session data for session continuation prediction.'
    )
    parser.add_argument('input_csv', type=str,
                        help='Path to annotated session CSV file.')
    parser.add_argument('--dataset', type=str, required=True,
                        choices=['aol', 'stackoverflow', 'movielens'],
                        help='Dataset format for user extraction.')
    parser.add_argument('--output-dir', type=str,
                        default='data/processed_session_continuation',
                        help='Output directory for train/val/test CSVs.')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility.')
    args = parser.parse_args()

    metadata = create_dataset(args.input_csv, args.dataset, args.output_dir, args.seed)
    print(f"\nDone! Train: {metadata['train_samples']}, "
          f"Val: {metadata['val_samples']}, Test: {metadata['test_samples']}")


if __name__ == '__main__':
    main()
