"""Domain-aware LLM agents for cognitive trace annotation."""

import json
import re
from typing import Any, Dict, List, Optional

from tracegen.config import TracGenConfig
from tracegen.llm.client import LLMClient
from tracegen.schemas.base import DomainSchema, VALID_LABELS


def _parse_json_array(response: str) -> List[Dict[str, Any]]:
    """Extract a JSON array from an LLM response string.

    Handles common LLM output issues:
    - Trailing commas before ] or }
    - Truncated output (uses last complete object)
    - Unquoted keys
    - Unescaped quotes inside string values
    """
    start = response.find("[")
    if start == -1:
        raise ValueError("No JSON array found in response")

    end = response.rfind("]")
    if end == -1:
        # Truncated output — find the last complete object (ending with })
        last_brace = response.rfind("}")
        if last_brace == -1:
            raise ValueError("No JSON array or complete objects found in response")
        raw = response[start:last_brace + 1] + "]"
    else:
        raw = response[start:end + 1]

    # Fix trailing commas: ,] or ,}
    raw = re.sub(r",\s*([}\]])", r"\1", raw)

    # Attempt 1: standard parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Attempt 2: fix unquoted keys
    try:
        fixed = re.sub(r'(?<=[{,])\s*(\w+)\s*:', r' "\1":', raw)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Attempt 3: extract objects individually via regex
    return _extract_objects_regex(response)


def _extract_objects_regex(response: str) -> List[Dict[str, Any]]:
    """Extract individual JSON-like objects from a malformed LLM response.

    Uses field-level regex to pull event_id, label, confidence, and justification
    from each object block, even when the overall JSON is broken.
    """
    # Split into object-like blocks (between { and })
    objects = []
    depth = 0
    current_start = None

    for i, ch in enumerate(response):
        if ch == "{":
            if depth == 0:
                current_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and current_start is not None:
                block = response[current_start:i + 1]
                obj = _extract_fields_from_block(block)
                if obj:
                    objects.append(obj)
                current_start = None

    if not objects:
        raise ValueError("Could not extract any valid objects from LLM response")
    return objects


def _extract_fields_from_block(block: str) -> Optional[Dict[str, Any]]:
    """Extract known fields from a single JSON-like object block."""
    # Try standard JSON parse first
    try:
        obj = json.loads(block)
        if "event_id" in obj or "label" in obj or "final_label" in obj:
            return obj
    except json.JSONDecodeError:
        pass

    # Regex extraction for known fields
    event_id = _extract_string_field(block, "event_id")
    label = _extract_string_field(block, "label") or _extract_string_field(block, "final_label")
    justification = _extract_string_field(block, "justification")
    confidence = _extract_number_field(block, "confidence")
    agreement = _extract_string_field(block, "agreement")
    flag = _extract_bool_field(block, "flag_for_review")

    if not label:
        return None

    obj: Dict[str, Any] = {}
    if event_id:
        obj["event_id"] = event_id
    if _extract_string_field(block, "final_label"):
        obj["final_label"] = label
    else:
        obj["label"] = label
    if justification:
        obj["justification"] = justification
    if confidence is not None:
        obj["confidence"] = confidence
    if agreement:
        obj["agreement"] = agreement
    if flag is not None:
        obj["flag_for_review"] = flag
    return obj


def _extract_string_field(block: str, field: str) -> Optional[str]:
    pattern = rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)(?:")'
    match = re.search(pattern, block, re.DOTALL)
    return match.group(1) if match else None


def _extract_number_field(block: str, field: str) -> Optional[float]:
    pattern = rf'"{field}"\s*:\s*([\d.]+)'
    match = re.search(pattern, block)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def _extract_bool_field(block: str, field: str) -> Optional[bool]:
    pattern = rf'"{field}"\s*:\s*(true|false)'
    match = re.search(pattern, block, re.IGNORECASE)
    if match:
        return match.group(1).lower() == "true"
    return None


def _estimate_max_tokens(n_events: int, base: int = 4096, per_event: int = 250, cap: int = 16000) -> int:
    return min(base + n_events * per_event, cap)


class DomainAnalystAgent:
    """Analyst agent that proposes initial cognitive labels using domain-specific prompts."""

    def __init__(self, client: LLMClient, schema: DomainSchema, config: TracGenConfig):
        self.client = client
        self.schema = schema
        self.config = config

    async def analyze(self, session_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze session events and propose cognitive labels."""
        events = self._apply_window(session_events)
        prompt = self.schema.get_analyst_prompt(events, self.config.window_size)
        max_tokens = _estimate_max_tokens(len(events))

        response_text, elapsed = await self.client.generate(
            self.config.analyst_model, prompt, max_tokens=max_tokens, role="analyst"
        )

        decisions = self._parse(response_text, events)
        return {
            "decisions": decisions,
            "raw_response": response_text,
            "elapsed_time": elapsed,
            "events_processed": len(events),
        }

    async def analyze_causal(self, session_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze session events with causal (event-by-event) annotation.

        For event t, only events[0:t+1] are visible to the LLM. This prevents
        temporal leakage where future events influence past labels.

        NOTE: This requires O(N) LLM calls per session instead of O(1),
        making it ~N times more expensive. Use for re-annotation experiments.
        """
        all_decisions = []
        total_elapsed = 0.0

        for t in range(len(session_events)):
            causal_prefix = session_events[: t + 1]
            prompt = self.schema.get_analyst_prompt_single_event(
                causal_prefix, target_index=t, window_size=self.config.window_size
            )
            max_tokens = _estimate_max_tokens(1)  # Only one event to label

            response_text, elapsed = await self.client.generate(
                self.config.analyst_model, prompt, max_tokens=max_tokens, role="analyst"
            )
            total_elapsed += elapsed

            parsed = _parse_json_array(response_text)
            if parsed:
                decision = parsed[0]
                label = decision.get("label", "")
                if label not in VALID_LABELS:
                    raise ValueError(
                        f"Invalid label '{label}' for event {t}. "
                        f"Valid labels: {', '.join(sorted(VALID_LABELS))}"
                    )
                eid = session_events[t].get("event_id", f"evt_{t}")
                all_decisions.append({
                    "event_id": eid,
                    "label": label,
                    "justification": decision.get("justification", ""),
                    "confidence": max(0.0, min(1.0, float(decision.get("confidence", 0.5)))),
                })
            else:
                raise ValueError(f"Could not parse LLM response for event {t}")

        return {
            "decisions": all_decisions,
            "raw_response": "(causal: one call per event)",
            "elapsed_time": total_elapsed,
            "events_processed": len(session_events),
        }

    def _apply_window(self, events: List[Dict]) -> List[Dict]:
        if self.config.session_strategy == "sliding_window" and len(events) > self.config.window_size:
            return events  # All events passed; sliding window note added to prompt
        return events

    def _parse(self, response: str, events: List[Dict]) -> List[Dict[str, Any]]:
        decisions = _parse_json_array(response)
        return self._align_decisions(decisions, events)

    def _align_decisions(self, decisions: List[Dict], events: List[Dict]) -> List[Dict]:
        """Ensure decisions match events 1:1 and have valid labels."""
        aligned = []
        event_ids = [e.get("event_id", f"evt_{i}") for i, e in enumerate(events)]

        # Build lookup by event_id
        decision_map = {}
        for d in decisions:
            eid = d.get("event_id", "")
            decision_map[eid] = d

        for i, eid in enumerate(event_ids):
            if eid in decision_map:
                d = decision_map[eid]
            elif i < len(decisions):
                d = decisions[i]
            else:
                raise ValueError(
                    f"LLM returned {len(decisions)} decisions but session has "
                    f"{len(events)} events. Missing decision for event '{eid}'."
                )

            label = d.get("label", "")
            if label not in VALID_LABELS:
                raise ValueError(
                    f"Invalid label '{label}' for event '{eid}'. "
                    f"Valid labels: {', '.join(sorted(VALID_LABELS))}"
                )

            aligned.append({
                "event_id": eid,
                "label": label,
                "justification": d.get("justification", ""),
                "confidence": max(0.0, min(1.0, float(d.get("confidence", 0.5)))),
            })
        return aligned


class DomainCriticAgent:
    """Critic agent that reviews and challenges the analyst's decisions."""

    def __init__(self, client: LLMClient, schema: DomainSchema, config: TracGenConfig):
        self.client = client
        self.schema = schema
        self.config = config

    async def review(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prompt = self.schema.get_critic_prompt(
            session_events, analyst_decisions, self.config.window_size
        )
        max_tokens = _estimate_max_tokens(len(session_events))

        response_text, elapsed = await self.client.generate(
            self.config.critic_model, prompt, max_tokens=max_tokens, role="critic"
        )

        decisions = self._parse(response_text, analyst_decisions)
        return {
            "decisions": decisions,
            "raw_response": response_text,
            "elapsed_time": elapsed,
        }

    def _parse(self, response: str, analyst_decisions: List[Dict]) -> List[Dict]:
        decisions = _parse_json_array(response)
        return self._align(decisions, analyst_decisions)

    def _align(self, decisions: List[Dict], analyst_decisions: List[Dict]) -> List[Dict]:
        aligned = []
        for i, ad in enumerate(analyst_decisions):
            if i < len(decisions):
                d = decisions[i]
            else:
                raise ValueError(
                    f"Critic returned {len(decisions)} decisions but analyst had "
                    f"{len(analyst_decisions)}. Missing decision for event '{ad.get('event_id', i)}'."
                )

            label = d.get("label", ad.get("label", ""))
            if label not in VALID_LABELS:
                raise ValueError(
                    f"Invalid critic label '{label}' for event '{ad.get('event_id', i)}'. "
                    f"Valid labels: {', '.join(sorted(VALID_LABELS))}"
                )

            aligned.append({
                "event_id": ad.get("event_id", f"evt_{i}"),
                "agreement": d.get("agreement", "agree"),
                "label": label,
                "justification": d.get("justification", ""),
                "confidence": max(0.0, min(1.0, float(d.get("confidence", 0.5)))),
            })
        return aligned


class DomainJudgeAgent:
    """Judge agent for final decision synthesis."""

    def __init__(self, client: LLMClient, schema: DomainSchema, config: TracGenConfig):
        self.client = client
        self.schema = schema
        self.config = config

    async def decide(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]],
        critic_decisions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prompt = self.schema.get_judge_prompt(
            session_events, analyst_decisions, critic_decisions, self.config.window_size
        )
        max_tokens = _estimate_max_tokens(len(session_events))

        response_text, elapsed = await self.client.generate(
            self.config.judge_model, prompt, max_tokens=max_tokens, role="judge"
        )

        decisions = self._parse(response_text, critic_decisions)
        return {
            "decisions": decisions,
            "raw_response": response_text,
            "elapsed_time": elapsed,
        }

    def _parse(self, response: str, critic_decisions: List[Dict]) -> List[Dict]:
        decisions = _parse_json_array(response)
        return self._align(decisions, critic_decisions)

    def _align(self, decisions: List[Dict], critic_decisions: List[Dict]) -> List[Dict]:
        aligned = []
        for i, cd in enumerate(critic_decisions):
            if i < len(decisions):
                d = decisions[i]
            else:
                raise ValueError(
                    f"Judge returned {len(decisions)} decisions but critic had "
                    f"{len(critic_decisions)}. Missing decision for event '{cd.get('event_id', i)}'."
                )

            label = d.get("final_label", "")
            if label not in VALID_LABELS:
                raise ValueError(
                    f"Invalid judge label '{label}' for event '{cd.get('event_id', i)}'. "
                    f"Valid labels: {', '.join(sorted(VALID_LABELS))}"
                )

            aligned.append({
                "event_id": cd.get("event_id", f"evt_{i}"),
                "final_label": label,
                "justification": d.get("justification", ""),
                "confidence": max(0.0, min(1.0, float(d.get("confidence", 0.5)))),
                "flag_for_review": d.get("flag_for_review", False),
            })
        return aligned
