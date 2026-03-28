"""Response format validator for LLM outputs."""

from typing import Any, Dict, List, Set

from tracegen.schemas.base import VALID_LABELS


class ResponseValidator:
    """Validates LLM response format and content."""

    @staticmethod
    def validate_analyst(decisions: List[Dict[str, Any]], expected_event_ids: Set[str]) -> List[str]:
        """Validate analyst decisions. Returns list of issues (empty = valid)."""
        issues = []

        if not decisions:
            issues.append("Empty decisions list")
            return issues

        if len(decisions) != len(expected_event_ids):
            issues.append(
                f"Event count mismatch: got {len(decisions)}, expected {len(expected_event_ids)}"
            )

        for i, d in enumerate(decisions):
            label = d.get("label", "")
            if label not in VALID_LABELS:
                issues.append(f"Event {i}: invalid label '{label}'")

            confidence = d.get("confidence")
            if confidence is not None:
                try:
                    c = float(confidence)
                    if not (0.0 <= c <= 1.0):
                        issues.append(f"Event {i}: confidence {c} out of [0,1]")
                except (ValueError, TypeError):
                    issues.append(f"Event {i}: non-numeric confidence '{confidence}'")

        return issues

    @staticmethod
    def validate_critic(decisions: List[Dict], n_events: int) -> List[str]:
        issues = []
        if len(decisions) != n_events:
            issues.append(f"Count mismatch: got {len(decisions)}, expected {n_events}")

        for i, d in enumerate(decisions):
            label = d.get("label", "")
            if label not in VALID_LABELS:
                issues.append(f"Event {i}: invalid label '{label}'")
            agreement = d.get("agreement", "")
            if agreement not in ("agree", "disagree"):
                issues.append(f"Event {i}: invalid agreement '{agreement}'")

        return issues

    @staticmethod
    def validate_judge(decisions: List[Dict], n_events: int) -> List[str]:
        issues = []
        if len(decisions) != n_events:
            issues.append(f"Count mismatch: got {len(decisions)}, expected {n_events}")

        for i, d in enumerate(decisions):
            label = d.get("final_label", "")
            if label not in VALID_LABELS:
                issues.append(f"Event {i}: invalid final_label '{label}'")

        return issues
