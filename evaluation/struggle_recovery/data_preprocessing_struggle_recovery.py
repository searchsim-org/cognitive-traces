#!/usr/bin/env python3
"""
Data preprocessing for Struggle Recovery Prediction

TASK: For sessions that START with zero-click behavior (user not engaging
with results), predict whether the user will eventually click a result
(recover) or abandon without clicking.

KEY INSIGHT: This tests whether behavioral patterns can predict recovery
trajectories. A user who starts without clicking might recover (eventually
engage with a result) or continue struggling. The behavioral signals
should help differentiate.

FILTER (purely behavioral):
- Session must start with zero-click behavior: no CLICK in the first 3 events
- This indicates the user is struggling to find relevant results

TARGET (purely behavioral):
- RECOVERY (1): Session eventually contains a CLICK (user engages with a result)
- NO RECOVERY (0): Session never has a CLICK (user abandons without engaging)

PRACTICAL UTILITY:
- Identify users who are likely to recover vs those who need help
- Allocate assistance resources efficiently
- Understand what behavioral patterns lead to recovery

DESIGN:
- Filter: Only sessions where first 3 events have no CLICK
- Input: First 60% of session events
- Target: 1 = session eventually has a CLICK
          0 = session never has a CLICK

This is distinct from previous tasks by focusing specifically on
recovery trajectories from initial struggle.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json


def get_user_from_session(session_id: str) -> str:
    """Extract user ID from session ID."""
    return session_id.split('_')[0] if '_' in session_id else session_id


def session_has_recovery(session_df: pd.DataFrame) -> bool:
    """Check if session eventually has a click (behavioral recovery)."""
    return (session_df['action_type'] == 'CLICK').any()


def create_recovery_samples(
    df: pd.DataFrame,
    prefix_ratio: float = 0.6,
    min_events: int = 4
) -> List[Dict]:
    """
    Create samples for struggle recovery prediction.

    Only includes sessions that START with zero-click behavior
    (no CLICK in first 3 events).
    """
    samples = []

    for session_id, session_df in df.groupby('session_id'):
        session_df = session_df.sort_values('event_timestamp').reset_index(drop=True)
        events = session_df.to_dict('records')

        # Filter: must start with zero-click behavior (no CLICK in first 3 events)
        early_actions = [e['action_type'] for e in events[:min(3, len(events))]]
        if 'CLICK' in early_actions:
            continue  # Session starts with clicking = not a struggle start

        # Filter: must have minimum events
        if len(events) < min_events:
            continue

        # Determine if session recovers
        recovers = session_has_recovery(session_df)
        target = 1 if recovers else 0

        # Take prefix
        n_prefix = max(3, int(len(events) * prefix_ratio))
        prefix_events = events[:n_prefix]

        # Analyze prefix patterns
        prefix_actions = [e['action_type'] for e in prefix_events]
        prefix_queries = sum(1 for a in prefix_actions if a == 'QUERY')
        prefix_clicks = sum(1 for a in prefix_actions if a == 'CLICK')

        sample = {
            'session_id': f"{session_id}_recovery",
            'original_session_id': session_id,
            'events': prefix_events,
            'target': target,
            'first_action': events[0]['action_type'],
            'full_length': len(events),
            'prefix_length': n_prefix,
            'prefix_query_count': prefix_queries,
            'prefix_click_count': prefix_clicks
        }
        samples.append(sample)

    return samples


def analyze_patterns(samples: List[Dict]) -> None:
    """Analyze recovery patterns based on behavioral signals."""
    print("\n=== STRUGGLE RECOVERY PATTERNS ===")

    # By first action type
    by_start = {}
    for s in samples:
        action = s['first_action']
        if action not in by_start:
            by_start[action] = {'recovers': 0, 'stays_struggle': 0}
        if s['target'] == 1:
            by_start[action]['recovers'] += 1
        else:
            by_start[action]['stays_struggle'] += 1

    print("\nBy first action:")
    for action in sorted(by_start.keys()):
        counts = by_start[action]
        total = counts['recovers'] + counts['stays_struggle']
        recover_pct = 100 * counts['recovers'] / total if total > 0 else 0
        print(f"  {action}: {recover_pct:.1f}% recover (n={total})")

    # By prefix click count
    print("\nBy prefix click count:")
    by_clicks = {}
    for s in samples:
        clicks = s['prefix_click_count']
        if clicks not in by_clicks:
            by_clicks[clicks] = {'recovers': 0, 'stays_struggle': 0}
        if s['target'] == 1:
            by_clicks[clicks]['recovers'] += 1
        else:
            by_clicks[clicks]['stays_struggle'] += 1

    for clicks in sorted(by_clicks.keys()):
        counts = by_clicks[clicks]
        total = counts['recovers'] + counts['stays_struggle']
        recover_pct = 100 * counts['recovers'] / total if total > 0 else 0
        print(f"  {clicks} clicks in prefix: {recover_pct:.1f}% recover (n={total})")


def balance_samples(samples: List[Dict], random_seed: int = 42) -> List[Dict]:
    """Balance recovery vs non-recovery samples."""
    np.random.seed(random_seed)

    recovers = [s for s in samples if s['target'] == 1]
    stays = [s for s in samples if s['target'] == 0]

    print(f"  Before: {len(recovers)} recover, {len(stays)} stay struggling")

    min_count = min(len(recovers), len(stays))

    if min_count < 5:
        print("  WARNING: Too few samples")
        return samples

    np.random.shuffle(recovers)
    np.random.shuffle(stays)

    balanced = recovers[:min_count] + stays[:min_count]
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
    output_dir: str = "data/processed_struggle_recovery",
    prefix_ratio: float = 0.6,
    random_seed: int = 42
) -> Dict:
    """Create balanced dataset for struggle recovery prediction."""
    np.random.seed(random_seed)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)

    print(f"Total events: {len(df)}")
    print(f"Total sessions: {df['session_id'].nunique()}")

    # Create samples
    print(f"\nCreating struggle recovery samples (sessions with zero-click start)...")
    all_samples = create_recovery_samples(df, prefix_ratio)
    print(f"Total samples: {len(all_samples)}")

    if len(all_samples) == 0:
        print("ERROR: No valid samples!")
        return {'train_samples': 0, 'val_samples': 0, 'test_samples': 0}

    # Distribution
    n_recover = sum(1 for s in all_samples if s['target'] == 1)
    n_stay = len(all_samples) - n_recover
    print(f"Distribution: {n_recover} recover ({100*n_recover/len(all_samples):.1f}%), "
          f"{n_stay} stay struggling ({100*n_stay/len(all_samples):.1f}%)")

    # Analyze patterns
    analyze_patterns(all_samples)

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

    # Assign samples
    train_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in train_users]
    val_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in val_users]
    test_samples = [s for s in all_samples if get_user_from_session(s['original_session_id']) in test_users]

    print(f"\nBefore balancing:")
    print(f"  Train: {len(train_samples)}")
    print(f"  Val: {len(val_samples)}")
    print(f"  Test: {len(test_samples)}")

    # Balance
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

        n_r = sum(1 for s in samples if s['target'] == 1)
        print(f"Saved {split_name}: {len(split_df)} rows, {len(samples)} samples "
              f"({n_r} recover, {len(samples)-n_r} stay struggling)")

    metadata = {
        'task': 'struggle_recovery_prediction',
        'description': 'For sessions starting with zero-click behavior, predict recovery (1) vs no recovery (0)',
        'filter_definition': 'Sessions where first 3 events have no CLICK (zero-click start)',
        'target_definition': 'RECOVERY (1) = session eventually has a CLICK; NO RECOVERY (0) = session never has a CLICK',
        'prefix_ratio': prefix_ratio,
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
    parser.add_argument('--output-dir', type=str, default='data/processed_struggle_recovery')
    parser.add_argument('--prefix-ratio', type=float, default=0.6)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    metadata = create_dataset(args.input_csv, args.output_dir, args.prefix_ratio, args.seed)
    print(f"\nDone! Train: {metadata['train_samples']}, Val: {metadata['val_samples']}, Test: {metadata['test_samples']}")


if __name__ == '__main__':
    main()
