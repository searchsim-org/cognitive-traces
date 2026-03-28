"""StackOverflow dataset loader — loads pre-built sessions from out_sessions/."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from tqdm import tqdm


class StackOverflowLoader:
    """Load pre-sessionized StackOverflow event logs.

    Filters out EDIT-dominated moderator sessions to ensure action type diversity.
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        max_sessions: Optional[int] = None,
        target_labels: int = 175_000,
        min_events: int = 3,
        max_events: int = 100,
    ):
        if data_dir is None:
            data_dir = str(
                Path(__file__).resolve().parent.parent.parent
                / "builder" / "data" / "stackoverflow" / "out_sessions"
            )
        self.data_dir = Path(data_dir)
        self.max_sessions = max_sessions
        self.target_labels = target_labels
        self.min_events = min_events
        self.max_events = max_events

    def load_sessions(self) -> List[Dict[str, Any]]:
        """Load sessions from the pre-built stackoverflow_sessions.csv."""
        sessions_file = self.data_dir / "stackoverflow_sessions.csv"

        if not sessions_file.exists():
            raise FileNotFoundError(
                f"SO sessions file not found at {sessions_file}. "
                "Run the builder first: subset-builder so ..."
            )

        print(f"[SO] Loading sessions from {sessions_file}...")

        target_session_ids = self._select_session_ids()

        # Read the full sessions CSV in chunks (it can be very large: 22.9GB)
        sessions_dict: Dict[str, List[Dict]] = {}
        chunk_iter = pd.read_csv(
            sessions_file,
            chunksize=500_000,
            dtype={"session_id": str, "user_id": str, "post_id": str, "parent_id": str},
        )

        for chunk in tqdm(chunk_iter, desc="[SO] Reading chunks", unit="chunk"):
            if target_session_ids is not None:
                chunk = chunk[chunk["session_id"].isin(target_session_ids)]

            for _, row in chunk.iterrows():
                sid = str(row["session_id"])
                if sid not in sessions_dict:
                    sessions_dict[sid] = []

                content = str(row.get("content", "")) if pd.notna(row.get("content")) else ""

                sessions_dict[sid].append({
                    "event_id": str(row.get("event_id", f"{sid}_{len(sessions_dict[sid])}")),
                    "timestamp": str(row.get("timestamp", "")),
                    "action_type": str(row.get("action_type", "UNKNOWN")),
                    "content": content[:500],
                })

            # Early exit if we have enough
            estimated_target = (self.max_sessions or (self.target_labels // 10))
            if len(sessions_dict) >= estimated_target:
                break

        # Convert to session list
        sessions = []
        for sid, events in sessions_dict.items():
            if self.min_events <= len(events) <= self.max_events:
                sessions.append({
                    "session_id": sid,
                    "events": events,
                })

        print(f"[SO] Loaded {len(sessions):,} sessions with {sum(len(s['events']) for s in sessions):,} total events")
        return sessions

    def _select_session_ids(self) -> Optional[Set[str]]:
        """Select diverse session IDs from the summary file.

        Filters out EDIT-dominated sessions (moderator/bot bulk edits)
        to ensure action type diversity for meaningful IFT labels.
        """
        summary_file = self.data_dir / "stackoverflow_sessions_summary.csv"
        if not summary_file.exists():
            print("[SO] No summary file found, loading all sessions...")
            return None

        summary_df = pd.read_csv(summary_file)

        # Filter by event count
        valid = summary_df[
            (summary_df["num_events"] >= self.min_events)
            & (summary_df["num_events"] <= self.max_events)
        ]

        # Filter out EDIT-dominated sessions: keep sessions where the
        # most frequent action type is NOT an EDIT action.
        # The top_actions column is ordered by frequency (most common first).
        def is_diverse(top_actions_str):
            first_action = str(top_actions_str).split(",")[0].strip()
            return "EDIT" not in first_action.upper()

        diverse = valid[valid["top_actions"].apply(is_diverse)]
        edit_heavy = len(valid) - len(diverse)

        print(f"[SO] {len(valid):,} sessions with {self.min_events}-{self.max_events} events")
        print(f"[SO] Filtered {edit_heavy:,} EDIT-dominated sessions, {len(diverse):,} diverse sessions remain")

        # Estimate sessions needed
        avg_events = diverse["num_events"].mean() if len(diverse) > 0 else 10
        estimated_sessions = int(self.target_labels / avg_events) + 500
        if self.max_sessions:
            estimated_sessions = min(estimated_sessions, self.max_sessions)

        # Sample sessions
        if len(diverse) > estimated_sessions:
            diverse = diverse.sample(n=estimated_sessions, random_state=42)

        target_ids = set(diverse["session_id"].tolist())
        print(f"[SO] Selected {len(target_ids):,} sessions (avg {avg_events:.0f} events)")
        return target_ids
