"""Live label distribution tracker with imbalance alerts."""

from collections import Counter
from typing import Dict, List, Any


class BalanceMonitor:
    """Tracks cognitive label distribution and raises alerts on imbalance."""

    def __init__(self, dataset_name: str, alert_threshold: float = 0.50):
        self.dataset_name = dataset_name
        self.alert_threshold = alert_threshold
        self.counts: Counter = Counter()
        self.total = 0
        self._alerted: set = set()

    def update(self, annotated_events: List[Dict[str, Any]]):
        """Update counts from a batch of annotated events."""
        for event in annotated_events:
            label = event.get("cognitive_label", "Unknown")
            self.counts[label] += 1
            self.total += 1

        self._check_alerts()

    def update_from_labels(self, labels: List[str]):
        """Update counts from a list of label strings."""
        for label in labels:
            self.counts[label] += 1
            self.total += 1
        self._check_alerts()

    def _check_alerts(self):
        if self.total < 100:
            return

        for label, count in self.counts.items():
            ratio = count / self.total
            if ratio > self.alert_threshold and label not in self._alerted:
                print(
                    f"[BALANCE ALERT] {self.dataset_name}: '{label}' is at {ratio:.1%} "
                    f"({count:,}/{self.total:,}) — exceeds {self.alert_threshold:.0%} threshold"
                )
                self._alerted.add(label)

    def get_distribution(self) -> Dict[str, float]:
        """Get current label distribution as percentages."""
        if self.total == 0:
            return {}
        return {label: count / self.total for label, count in self.counts.most_common()}

    def get_counts(self) -> Dict[str, int]:
        """Get raw label counts."""
        return dict(self.counts)

    def summary_line(self) -> str:
        """One-line summary for progress display."""
        if self.total == 0:
            return "No labels yet"
        parts = []
        abbrev = {
            "FollowingScent": "FS",
            "ApproachingSource": "AS",
            "DietEnrichment": "DE",
            "PoorScent": "PS",
            "LeavingPatch": "LP",
            "ForagingSuccess": "FgS",
        }
        for label, count in self.counts.most_common():
            short = abbrev.get(label, label[:3])
            pct = count / self.total * 100
            parts.append(f"{short}={pct:.0f}%")
        return " ".join(parts)
