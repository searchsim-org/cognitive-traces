#!/usr/bin/env python3
"""
Quick quality test: annotate a small sample from each dataset and compare
label distributions against the old imbalanced traces.

Usage:
    python -m tracegen.test_quality [--sessions N] [--model MODEL]
"""

import asyncio
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# ── project imports ──
from tracegen.config import load_config
from tracegen.llm.client import LLMClient
from tracegen.llm.agents import DomainAnalystAgent
from tracegen.schemas.aol import AOLSchema
from tracegen.schemas.stackoverflow import StackOverflowSchema
from tracegen.schemas.movielens import MovieLensSchema

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


# ── old trace baselines (from existing annotated CSVs) ──
OLD_BASELINES = {
    "aol": {
        "PoorScent": 67.2, "ApproachingSource": 20.4, "LeavingPatch": 10.9,
        "DietEnrichment": 0.9, "FollowingScent": 0.6, "ForagingSuccess": 0.0,
    },
    "stackoverflow": {
        "DietEnrichment": 10.5, "FollowingScent": 7.5, "ForagingSuccess": 3.9,
        "PoorScent": 0.9, "ApproachingSource": 0.1,
    },
    "movielens": {
        "PoorScent": 42.4, "FollowingScent": 27.4, "ForagingSuccess": 16.3,
        "DietEnrichment": 16.1, "ApproachingSource": 3.6, "LeavingPatch": 2.6,
    },
}


def load_aol_sessions(n: int = 5) -> List[Dict[str, Any]]:
    """Load N sessions from the AOL input CSV."""
    df = pd.read_csv(DATA_DIR / "aol_1k_input.csv")
    session_ids = df["session_id"].unique()[:n]
    sessions = []
    for sid in session_ids:
        group = df[df["session_id"] == sid]
        events = []
        for _, row in group.iterrows():
            events.append({
                "event_id": str(row["event_id"]),
                "timestamp": str(row["timestamp"]),
                "action_type": str(row["action_type"]),
                "content": str(row.get("content", ""))[:300],
            })
        if len(events) >= 2:
            sessions.append({"session_id": str(sid), "events": events})
    return sessions


def load_so_sessions(n: int = 5) -> List[Dict[str, Any]]:
    """Load N sessions from the SO input CSV."""
    df = pd.read_csv(DATA_DIR / "stackoverflow_input.csv")
    session_ids = df["session_id"].unique()[:n * 3]  # sample more, filter by size
    sessions = []
    for sid in session_ids:
        group = df[df["session_id"] == sid]
        events = []
        for _, row in group.iterrows():
            events.append({
                "event_id": str(row["event_id"]),
                "timestamp": str(row["timestamp"]),
                "action_type": str(row["action_type"]),
                "content": str(row.get("content", ""))[:300],
            })
        if 3 <= len(events) <= 30:
            sessions.append({"session_id": str(sid), "events": events})
        if len(sessions) >= n:
            break
    return sessions


def load_ml_sessions(n: int = 5) -> List[Dict[str, Any]]:
    """Load N sessions from the MovieLens input CSV."""
    df = pd.read_csv(DATA_DIR / "movielens_input.csv")
    session_ids = df["session_id"].unique()[:n * 3]
    sessions = []
    for sid in session_ids:
        group = df[df["session_id"] == sid]
        events = []
        for _, row in group.iterrows():
            events.append({
                "event_id": str(row["event_id"]),
                "timestamp": str(row["timestamp"]),
                "action_type": str(row["action_type"]),
                "content": str(row.get("content", ""))[:300],
            })
        if 3 <= len(events) <= 30:
            sessions.append({"session_id": str(sid), "events": events})
        if len(sessions) >= n:
            break
    return sessions


async def annotate_sessions(
    sessions: List[Dict],
    schema,
    client: LLMClient,
    config,
    label: str,
) -> Counter:
    """Run analyst on sessions, return label counts."""
    agent = DomainAnalystAgent(client, schema, config)
    all_labels: Counter = Counter()
    total_events = 0

    for i, session in enumerate(sessions):
        sid = session["session_id"]
        n_events = len(session["events"])
        print(f"  [{label}] Session {i+1}/{len(sessions)}: {sid} ({n_events} events)...", end=" ", flush=True)

        t0 = time.time()
        try:
            result = await agent.analyze(session["events"])
            elapsed = time.time() - t0
            decisions = result["decisions"]

            for d in decisions:
                all_labels[d.get("label", "Unknown")] += 1
                total_events += 1

            labels_in_session = Counter(d["label"] for d in decisions)
            summary = ", ".join(f"{l}:{c}" for l, c in labels_in_session.most_common(3))
            print(f"OK ({elapsed:.1f}s) -> {summary}")

        except Exception as e:
            print(f"FAILED: {e}")

    return all_labels


def print_comparison(dataset: str, new_dist: Counter, total: int):
    """Print side-by-side comparison with old baseline."""
    old = OLD_BASELINES.get(dataset, {})

    all_labels = sorted(
        set(list(new_dist.keys()) + list(old.keys())),
        key=lambda x: new_dist.get(x, 0),
        reverse=True,
    )

    print(f"\n{'Label':<22} {'OLD %':>8} {'NEW %':>8} {'NEW #':>7}  {'Change':>10}")
    print("-" * 62)

    for label in all_labels:
        old_pct = old.get(label, 0.0)
        new_pct = new_dist[label] / max(total, 1) * 100 if total > 0 else 0
        count = new_dist.get(label, 0)
        delta = new_pct - old_pct

        if abs(delta) < 0.1:
            arrow = "   ~"
        elif delta > 0:
            arrow = f"  +{delta:+.1f}%"
        else:
            arrow = f"  {delta:+.1f}%"

        print(f"  {label:<20} {old_pct:>7.1f}% {new_pct:>7.1f}% {count:>6}   {arrow}")

    # Imbalance ratio
    if len(new_dist) > 1 and total > 0:
        pcts = [c / total * 100 for c in new_dist.values()]
        ratio = max(pcts) / max(min(pcts), 0.01)
        old_ratio_vals = [v for v in old.values() if v > 0]
        old_ratio = max(old_ratio_vals) / max(min(old_ratio_vals), 0.01) if old_ratio_vals else 999

        print(f"\n  Imbalance ratio:  OLD {old_ratio:.1f}:1  ->  NEW {ratio:.1f}:1")
        if ratio < old_ratio:
            improvement = (1 - ratio / old_ratio) * 100
            print(f"  Improvement: {improvement:.0f}% reduction in imbalance")


async def run_test(n_sessions: int = 3, model: str = "gpt-4o-mini"):
    """Run the full quality test."""
    print("=" * 70)
    print("QUALITY TEST — Domain-Adapted IFT Schema vs Old Generic Schema")
    print("=" * 70)
    print(f"Sessions per dataset: {n_sessions}")
    print(f"Model: {model}")
    print(f"Mode: analyst-only (single pass for speed)")
    print()

    # Load config
    config = load_config()
    config.analyst_model = model
    config.temperature = 0.3
    config.verbose = True

    # Use OpenAI for reliability in test
    client = LLMClient(config)

    datasets = [
        ("aol", AOLSchema(), load_aol_sessions(n_sessions)),
        ("stackoverflow", StackOverflowSchema(), load_so_sessions(n_sessions)),
        ("movielens", MovieLensSchema(), load_ml_sessions(n_sessions)),
    ]

    overall_old_total = Counter()
    overall_new_total = Counter()
    grand_total = 0

    for dataset_name, schema, sessions in datasets:
        print(f"\n{'─' * 70}")
        print(f"DATASET: {dataset_name.upper()} ({len(sessions)} sessions, "
              f"{sum(len(s['events']) for s in sessions)} events)")
        print(f"{'─' * 70}")

        if not sessions:
            print("  No sessions loaded. Skipping.")
            continue

        new_labels = await annotate_sessions(sessions, schema, client, config, dataset_name)
        total = sum(new_labels.values())
        grand_total += total

        for label, count in new_labels.items():
            overall_new_total[label] += count

        print_comparison(dataset_name, new_labels, total)

    # Overall summary
    print(f"\n{'=' * 70}")
    print("OVERALL SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total events annotated: {grand_total}")
    print(f"\nNew label distribution across all datasets:")
    for label, count in overall_new_total.most_common():
        pct = count / max(grand_total, 1) * 100
        bar = "#" * int(pct / 2)
        print(f"  {label:<20} {count:>6} ({pct:5.1f}%) {bar}")

    if grand_total > 0 and len(overall_new_total) > 1:
        pcts = [c / grand_total * 100 for c in overall_new_total.values()]
        ratio = max(pcts) / max(min(pcts), 0.01)
        print(f"\n  Overall imbalance ratio: {ratio:.1f}:1")
        severity = "GOOD" if ratio < 5 else "MODERATE" if ratio < 20 else "SEVERE"
        print(f"  Severity: {severity}")
        print(f"  (Old combined imbalance was ~1485:1 SEVERE)")

    print(f"\n{'=' * 70}")


def main():
    n_sessions = 3
    model = "gpt-4o-mini"

    # Parse simple args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--sessions" and i + 1 < len(args):
            n_sessions = int(args[i + 1])
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        else:
            i += 1

    asyncio.run(run_test(n_sessions=n_sessions, model=model))


if __name__ == "__main__":
    main()
