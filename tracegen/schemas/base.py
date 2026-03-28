"""Base schema types for cognitive trace annotation."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any


class CognitiveLabel(str, Enum):
    """Cognitive labels based on Information Foraging Theory."""
    FOLLOWING_SCENT = "FollowingScent"
    APPROACHING_SOURCE = "ApproachingSource"
    DIET_ENRICHMENT = "DietEnrichment"
    POOR_SCENT = "PoorScent"
    LEAVING_PATCH = "LeavingPatch"
    FORAGING_SUCCESS = "ForagingSuccess"


VALID_LABELS = {label.value for label in CognitiveLabel}


class DomainSchema(ABC):
    """Abstract base for domain-specific IFT annotation schemas."""

    domain: str
    action_types: List[str]

    @abstractmethod
    def get_label_schema_text(self) -> str:
        """Return the domain-adapted label schema as a prompt string."""
        ...

    def get_analyst_prompt(self, session_events: List[Dict[str, Any]], window_size: int = 30) -> str:
        """Build the analyst prompt for a session."""
        content_limit = self._content_limit(len(session_events))
        sliding_note = self._sliding_window_note(len(session_events), window_size)

        events_str = self._format_events(session_events, content_limit)

        return f"""You are an expert behavioral analyst specializing in Information Foraging Theory. Your task is to analyze user behavior and assign cognitive labels to each event in the session.

{self.get_label_schema_text()}
{sliding_note}
## Session to Analyze:
{events_str}

## Your Task:
For EACH event in the session, provide:
1. The most appropriate cognitive label
2. Step-by-step justification for your choice
3. Confidence score (0.0-1.0)

## Output Format (JSON):
Return a JSON array with one object per event:
```json
[
  {{
    "event_id": "...",
    "label": "FollowingScent",
    "justification": "Step-by-step reasoning...",
    "confidence": 0.85
  }}
]
```

Provide ONLY the JSON array, no additional text. MUST include all {len(session_events)} events in your response."""

    def get_critic_prompt(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]],
        window_size: int = 30,
    ) -> str:
        """Build the critic prompt for reviewing analyst decisions."""
        content_limit = self._content_limit(len(session_events))
        reasoning_limit = self._reasoning_limit(len(session_events))
        sliding_note = self._sliding_window_note(len(session_events), window_size)

        analysis_str = ""
        for i, (event, decision) in enumerate(zip(session_events, analyst_decisions), 1):
            content = str(event.get("content", ""))[:content_limit]
            justification = str(decision.get("justification", ""))[:reasoning_limit]
            analysis_str += (
                f"\nEvent {i}:\n"
                f"  - Action: {event.get('action_type', '')}\n"
                f"  - Content: {content}...\n"
                f"  - Analyst's Label: {decision.get('label', '')}\n"
                f"  - Analyst's Reasoning: {justification}...\n"
            )

        return f"""You are a critical reviewer specializing in Information Foraging Theory. Your role is to challenge and review the Analyst's cognitive label assignments.

{self.get_label_schema_text()}
{sliding_note}
## Analyst's Analysis:
{analysis_str}

## Your Task:
For EACH event, either:
1. AGREE with the Analyst's label and provide brief supporting argument
2. DISAGREE and propose a different label with counter-argument

Be thorough and question assumptions. Look for alternative explanations.

## Output Format (JSON):
```json
[
  {{
    "event_id": "...",
    "agreement": "agree",
    "label": "FollowingScent",
    "justification": "Reasoning for agreement or alternative explanation...",
    "confidence": 0.80
  }}
]
```

Provide ONLY the JSON array, no additional text. MUST include all {len(session_events)} events in your response."""

    def get_judge_prompt(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]],
        critic_decisions: List[Dict[str, Any]],
        window_size: int = 30,
    ) -> str:
        """Build the judge prompt for final arbitration."""
        content_limit = self._content_limit(len(session_events))
        reasoning_limit = self._reasoning_limit(len(session_events))
        sliding_note = self._sliding_window_note(len(session_events), window_size)

        deliberation_str = ""
        for i, (event, analyst, critic) in enumerate(
            zip(session_events, analyst_decisions, critic_decisions), 1
        ):
            content = str(event.get("content", ""))[:content_limit]
            a_just = str(analyst.get("justification", ""))[:reasoning_limit]
            c_just = str(critic.get("justification", ""))[:reasoning_limit]
            deliberation_str += (
                f"\nEvent {i} ({event.get('event_id', '')}):\n"
                f"  - Action: {event.get('action_type', '')}\n"
                f"  - Content: {content}...\n"
                f"  - Analyst: {analyst.get('label', '')} (confidence: {analyst.get('confidence', 0)})\n"
                f"    Reasoning: {a_just}...\n"
                f"  - Critic: {critic.get('agreement', '')} - {critic.get('label', '')} "
                f"(confidence: {critic.get('confidence', 0)})\n"
                f"    Reasoning: {c_just}...\n"
            )

        return f"""You are the final arbiter in a multi-agent cognitive labeling system. Your role is to synthesize the Analyst's and Critic's perspectives and make the final decision.

{self.get_label_schema_text()}
{sliding_note}
## Agent Deliberations:
{deliberation_str}

## Your Task:
For EACH event, provide:
1. Your FINAL cognitive label decision
2. Comprehensive justification synthesizing both perspectives
3. Final confidence score
4. Flag for human review if there's significant disagreement

## Output Format (JSON):
```json
[
  {{
    "event_id": "...",
    "final_label": "FollowingScent",
    "justification": "Comprehensive synthesis of all perspectives...",
    "confidence": 0.87,
    "flag_for_review": false
  }}
]
```

Provide ONLY the JSON array, no additional text. MUST include all {len(session_events)} events in your response."""

    def get_analyst_prompt_single_event(
        self,
        causal_prefix: List[Dict[str, Any]],
        target_index: int,
        window_size: int = 30,
    ) -> str:
        """Build an analyst prompt that labels ONLY the last event in the prefix.

        Used for causal annotation: the LLM sees events[0:t+1] and labels
        only event t. This prevents temporal leakage from future events.
        """
        content_limit = self._content_limit(len(causal_prefix))
        context_events = causal_prefix[:-1]
        target_event = causal_prefix[-1]

        context_str = ""
        if context_events:
            context_str = "\n## Prior Context (already labeled — for reference only):\n"
            for i, event in enumerate(context_events, 1):
                content = str(event.get("content", ""))[:content_limit]
                context_str += (
                    f"\nEvent {i}:\n"
                    f"  - Action: {event.get('action_type', '')}\n"
                    f"  - Content: {content}...\n"
                )

        target_str = (
            f"\n## Event to Label (Event {target_index + 1}):\n"
            f"  - ID: {target_event.get('event_id', '')}\n"
            f"  - Timestamp: {target_event.get('timestamp', '')}\n"
            f"  - Action: {target_event.get('action_type', '')}\n"
            f"  - Content: {str(target_event.get('content', ''))[:content_limit]}...\n"
        )

        return f"""You are an expert behavioral analyst specializing in Information Foraging Theory. Your task is to assign a cognitive label to ONE specific event, using only events that occurred BEFORE or AT this point in the session.

{self.get_label_schema_text()}
{context_str}
{target_str}

## Your Task:
Assign the most appropriate cognitive label to Event {target_index + 1} based ONLY on what has happened so far (no future knowledge).

## Output Format (JSON):
```json
[
  {{
    "event_id": "{target_event.get('event_id', '')}",
    "label": "FollowingScent",
    "justification": "Step-by-step reasoning based on events so far...",
    "confidence": 0.85
  }}
]
```

Provide ONLY the JSON array with exactly 1 object."""

    # ── helpers ──

    def _format_events(self, events: List[Dict[str, Any]], content_limit: int) -> str:
        lines = ""
        for i, event in enumerate(events, 1):
            content = str(event.get("content", ""))[:content_limit]
            lines += (
                f"\nEvent {i}:\n"
                f"  - ID: {event.get('event_id', '')}\n"
                f"  - Timestamp: {event.get('timestamp', '')}\n"
                f"  - Action: {event.get('action_type', '')}\n"
                f"  - Content: {content}...\n"
            )
        return lines

    @staticmethod
    def _content_limit(n_events: int) -> int:
        if n_events <= 20:
            return 200
        elif n_events <= 50:
            return 150
        return 100

    @staticmethod
    def _reasoning_limit(n_events: int) -> int:
        if n_events <= 20:
            return 300
        elif n_events <= 50:
            return 200
        return 150

    @staticmethod
    def _sliding_window_note(n_events: int, window_size: int) -> str:
        if n_events <= window_size:
            return ""
        return f"""
## Important - Sliding Window Context:
When analyzing each event, only consider the previous {window_size} events as context.
You must still annotate ALL {n_events} events.
"""
