"""Checkpoint manager for pause/resume support."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

from tracegen.config import TracGenConfig


class CheckpointManager:
    """Manages per-dataset checkpoint state for reliable resume."""

    def __init__(self, config: TracGenConfig, dataset_name: str):
        self.dataset_name = dataset_name
        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.checkpoint_dir / f"{dataset_name}_checkpoint.json"
        self.config_hash = config.config_hash
        self._completed: Set[str] = set()
        self._label_distribution: Dict[str, int] = {}
        self._errors: list = []
        self._save_counter = 0
        self._save_interval = 10  # Save every N sessions

    def load(self) -> Set[str]:
        """Load completed session IDs from existing checkpoint."""
        if not self.path.exists():
            return set()

        try:
            data = json.loads(self.path.read_text())
            self._completed = set(data.get("completed_session_ids", []))
            self._label_distribution = data.get("label_distribution", {})
            self._errors = data.get("errors", [])

            # Warn if config changed
            saved_hash = data.get("config_hash", "")
            if saved_hash and saved_hash != self.config_hash:
                print(
                    f"[WARN] {self.dataset_name}: Config changed since last checkpoint. "
                    "Labels generated with different settings may be mixed."
                )

            print(
                f"[CHECKPOINT] {self.dataset_name}: Resuming with "
                f"{len(self._completed):,} completed sessions"
            )
            return self._completed

        except Exception as e:
            print(f"[WARN] Failed to load checkpoint {self.path}: {e}")
            return set()

    def mark_complete(
        self,
        session_id: str,
        label_counts: Optional[Dict[str, int]] = None,
    ):
        """Mark a session as completed and optionally update label distribution."""
        self._completed.add(session_id)
        if label_counts:
            for label, count in label_counts.items():
                self._label_distribution[label] = self._label_distribution.get(label, 0) + count

        self._save_counter += 1
        if self._save_counter >= self._save_interval:
            self.save()
            self._save_counter = 0

    def record_error(self, session_id: str, error: str):
        self._errors.append({"session_id": session_id, "error": error[:500], "time": datetime.now().isoformat()})

    def save(self):
        """Atomic save: write to temp, then rename."""
        data = {
            "dataset": self.dataset_name,
            "completed_session_ids": list(self._completed),
            "completed_count": len(self._completed),
            "label_distribution": self._label_distribution,
            "config_hash": self.config_hash,
            "errors": self._errors[-100:],  # Keep last 100 errors
            "timestamp": datetime.now().isoformat(),
        }

        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, indent=2))
        os.replace(str(tmp_path), str(self.path))

    def force_save(self):
        """Force an immediate save (e.g., on graceful shutdown)."""
        self.save()

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    @property
    def label_distribution(self) -> Dict[str, int]:
        return dict(self._label_distribution)

    @property
    def error_count(self) -> int:
        return len(self._errors)
