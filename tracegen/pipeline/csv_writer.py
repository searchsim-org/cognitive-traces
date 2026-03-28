"""Incremental CSV writer for annotation output."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from tracegen.config import TracGenConfig


CSV_HEADER = [
    "session_id",
    "event_id",
    "event_timestamp",
    "action_type",
    "content",
    "cognitive_label",
    "analyst_label",
    "analyst_justification",
    "critic_label",
    "critic_agreement",
    "critic_justification",
    "judge_justification",
    "confidence_score",
    "disagreement_score",
    "flagged_for_review",
    "pipeline_mode",
]


class CSVWriter:
    """Thread-safe incremental CSV writer."""

    def __init__(self, config: TracGenConfig, dataset_name: str):
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / f"{dataset_name}_cognitive_traces.csv"
        self._initialized = False

    def _ensure_header(self):
        """Write header if file doesn't exist yet."""
        if self._initialized:
            return
        if not self.output_file.exists():
            with open(self.output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(CSV_HEADER)
        self._initialized = True

    def append(self, result: Dict[str, Any]):
        """Append annotated events from a session result to the CSV."""
        self._ensure_header()

        events = result.get("annotated_events", [])
        pipeline_mode = result.get("pipeline_mode", "adaptive")

        with open(self.output_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            for event in events:
                row = [
                    event.get("session_id", ""),
                    event.get("event_id", ""),
                    event.get("timestamp", ""),
                    event.get("action_type", ""),
                    str(event.get("content", ""))[:500],
                    event.get("cognitive_label", ""),
                    event.get("analyst_label", ""),
                    str(event.get("analyst_justification", ""))[:500],
                    event.get("critic_label", ""),
                    event.get("critic_agreement", ""),
                    str(event.get("critic_justification", ""))[:500],
                    str(event.get("judge_justification", ""))[:500],
                    event.get("confidence_score", 0.0),
                    event.get("disagreement_score", 0.0),
                    event.get("flagged_for_review", False),
                    pipeline_mode,
                ]
                writer.writerow(row)

    @property
    def path(self) -> Path:
        return self.output_file
