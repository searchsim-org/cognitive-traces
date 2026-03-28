"""Post-generation sanity check and distribution report."""

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from tracegen.config import TracGenConfig
from tracegen.schemas.base import VALID_LABELS


def check_dataset(config: TracGenConfig, dataset: Optional[str] = None, file_path: Optional[str] = None):
    """Run sanity checks on generated cognitive traces."""
    if file_path:
        csv_path = Path(file_path)
    elif dataset:
        csv_path = Path(config.output_dir) / f"{dataset}_cognitive_traces.csv"
    else:
        # Check all datasets
        for ds in ["aol", "stackoverflow", "movielens"]:
            p = Path(config.output_dir) / f"{ds}_cognitive_traces.csv"
            if p.exists():
                _check_single(p, ds)
        return

    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return

    _check_single(csv_path, dataset or csv_path.stem)


def _check_single(csv_path: Path, name: str):
    """Run checks on a single output CSV."""
    print("=" * 70)
    print(f"SANITY CHECK: {name}")
    print("=" * 70)

    df = pd.read_csv(csv_path)

    # Basic stats
    n_events = len(df)
    n_sessions = df["session_id"].nunique()
    print(f"\n  Total events:    {n_events:,}")
    print(f"  Total sessions:  {n_sessions:,}")
    print(f"  Avg events/sess: {n_events / max(n_sessions, 1):.1f}")

    # Label distribution
    label_col = "cognitive_label"
    if label_col not in df.columns:
        print(f"\n  [ERROR] Column '{label_col}' not found in CSV")
        return

    dist = df[label_col].value_counts()
    dist_pct = df[label_col].value_counts(normalize=True) * 100

    print(f"\n  LABEL DISTRIBUTION:")
    for label in dist.index:
        count = dist[label]
        pct = dist_pct[label]
        bar = "#" * int(pct / 2)
        valid_marker = "OK" if label in VALID_LABELS else "INVALID"
        print(f"    {label:20s} {count:>8,} ({pct:5.1f}%) [{valid_marker}] {bar}")

    # Invalid labels
    invalid = df[~df[label_col].isin(VALID_LABELS)]
    if len(invalid) > 0:
        print(f"\n  [WARN] {len(invalid):,} events with invalid labels")

    # Missing labels
    missing = df[df[label_col].isna()]
    if len(missing) > 0:
        print(f"\n  [WARN] {len(missing):,} events with missing labels")

    # Imbalance ratio
    if len(dist) > 1:
        max_pct = dist_pct.max()
        min_pct = dist_pct.min()
        ratio = max_pct / max(min_pct, 0.01)
        status = "GOOD" if ratio < 5 else "MODERATE" if ratio < 20 else "SEVERE"
        print(f"\n  Imbalance ratio:  {ratio:.1f}:1 ({status})")
        print(f"    Most common:    {dist.index[0]} ({max_pct:.1f}%)")
        print(f"    Least common:   {dist.index[-1]} ({min_pct:.1f}%)")

    # Confidence stats
    if "confidence_score" in df.columns:
        conf = pd.to_numeric(df["confidence_score"], errors="coerce")
        print(f"\n  CONFIDENCE SCORES:")
        print(f"    Mean:           {conf.mean():.3f}")
        print(f"    Median:         {conf.median():.3f}")
        print(f"    < 0.5:          {(conf < 0.5).sum():,} events ({(conf < 0.5).mean() * 100:.1f}%)")
        print(f"    >= 0.8:         {(conf >= 0.8).sum():,} events ({(conf >= 0.8).mean() * 100:.1f}%)")

    # Flagged for review
    if "flagged_for_review" in df.columns:
        flagged = df["flagged_for_review"].astype(str).str.lower().isin(["true", "1"])
        print(f"\n  Flagged for review: {flagged.sum():,} ({flagged.mean() * 100:.1f}%)")

    # Pipeline mode distribution
    if "pipeline_mode" in df.columns:
        mode_dist = df["pipeline_mode"].value_counts()
        print(f"\n  PIPELINE MODE:")
        for mode, count in mode_dist.items():
            print(f"    {mode:20s} {count:>8,} ({count / n_events * 100:.1f}%)")

    # Action type distribution
    if "action_type" in df.columns:
        action_dist = df["action_type"].value_counts()
        print(f"\n  ACTION TYPES:")
        for action, count in action_dist.items():
            print(f"    {action:25s} {count:>8,}")

    print("\n" + "=" * 70)

    # Save report as JSON
    report_path = csv_path.with_suffix(".report.json")
    report = {
        "dataset": name,
        "total_events": n_events,
        "total_sessions": n_sessions,
        "label_distribution": dist.to_dict(),
        "label_percentages": dist_pct.to_dict(),
        "invalid_labels": len(invalid),
        "missing_labels": len(missing),
    }
    report_path.write_text(json.dumps(report, indent=2))
    print(f"  Report saved to: {report_path}")
