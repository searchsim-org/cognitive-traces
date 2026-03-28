"""Progress display utilities."""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional

from tracegen.config import TracGenConfig


def _is_pipeline_running() -> bool:
    """Check if a tracegen pipeline process is currently running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python.*-m tracegen (run|resume)"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def show_status(config: TracGenConfig):
    """Show checkpoint status for all datasets."""
    checkpoint_dir = Path(config.checkpoint_dir)
    if not checkpoint_dir.exists():
        print("No checkpoints found.")
        return

    running = _is_pipeline_running()

    print("=" * 70)
    if running:
        print("Checkpoint Status  [PIPELINE RUNNING]")
    else:
        print("Checkpoint Status  [PIPELINE STOPPED]")
    print("=" * 70)

    found = False
    for dataset in ["aol", "stackoverflow", "movielens"]:
        cp_file = checkpoint_dir / f"{dataset}_checkpoint.json"
        if not cp_file.exists():
            continue

        found = True
        data = json.loads(cp_file.read_text())
        completed = data.get("completed_count", 0)
        dist = data.get("label_distribution", {})
        error_list = data.get("errors", [])
        ts = data.get("timestamp", "unknown")

        total_labels = sum(dist.values())
        target = config.get_target(dataset)
        pct_done = total_labels / max(target, 1) * 100

        print(f"\n  {dataset.upper()}")
        print(f"    Progress: {total_labels:,} / {target:,} labels ({pct_done:.1f}%)")
        print(f"    Completed sessions: {completed:,}")
        print(f"    Errors: {len(error_list)}")
        print(f"    Last save: {ts}")

        if dist:
            print("    Label distribution:")
            for label, count in sorted(dist.items(), key=lambda x: -x[1]):
                pct = count / max(total_labels, 1) * 100
                bar = "#" * int(pct / 2)
                print(f"      {label:20s} {count:>7,} ({pct:5.1f}%) {bar}")

        if error_list:
            print(f"    Recent errors (last {min(3, len(error_list))}):")
            for err in error_list[-3:]:
                print(f"      [{err.get('session_id', '?')}] {err.get('error', '')[:100]}")

    # Check for output CSVs
    output_dir = Path(config.output_dir)
    if output_dir.exists():
        print("\n  OUTPUT FILES:")
        for csv_file in sorted(output_dir.glob("*_cognitive_traces.csv")):
            size_mb = csv_file.stat().st_size / 1024 / 1024
            print(f"    {csv_file.name}: {size_mb:.1f} MB")

    if not found:
        print("  No checkpoint files found.")

    print("=" * 70)
