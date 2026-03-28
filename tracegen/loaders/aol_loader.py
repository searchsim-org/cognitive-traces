"""AOL search dataset loader — builds sessions from raw data.csv + query.csv + doc.csv."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from tqdm import tqdm


class AOLLoader:
    """Load and sessionize AOL search query log data.

    Prioritises complex sessions (3+ unique queries) to ensure label diversity.
    Deduplicates QUERY/SERP_VIEW events per QueryIndex within each session.
    """

    # Minimum unique queries for a session to be considered "complex"
    MIN_COMPLEX_QUERIES = 3

    def __init__(
        self,
        data_dir: Optional[str] = None,
        max_sessions: Optional[int] = None,
        target_labels: int = 200_000,
    ):
        if data_dir is None:
            data_dir = str(Path(__file__).resolve().parent.parent.parent / "builder" / "data" / "aol")
        self.data_dir = Path(data_dir)
        self.max_sessions = max_sessions
        self.target_labels = target_labels

    def load_sessions(self) -> List[Dict[str, Any]]:
        """Load raw AOL data and convert to session format."""
        print("[AOL] Loading raw data files...")

        data_df = pd.read_csv(self.data_dir / "data.csv", sep="\t")
        query_df = pd.read_csv(self.data_dir / "query.csv", sep="\t")
        doc_df = pd.read_csv(self.data_dir / "doc.csv", sep="\t")

        print(f"[AOL] Loaded {len(data_df):,} interactions, {len(query_df):,} queries, {len(doc_df):,} docs")

        # Merge query text and doc info
        data_df = data_df.merge(query_df[["QueryIndex", "Query"]], on="QueryIndex", how="left")
        data_df = data_df.merge(doc_df[["DocIndex", "Url", "Title"]], on="DocIndex", how="left")

        # Create session_id
        data_df["session_id"] = data_df["AnonID"].astype(str) + "_" + data_df["SessionNo"].astype(str)

        # Count unique queries per session to identify complex sessions
        session_query_counts = data_df.groupby("session_id")["QueryIndex"].nunique()
        complex_sids = set(session_query_counts[session_query_counts >= self.MIN_COMPLEX_QUERIES].index)
        simple_sids = set(session_query_counts[
            (session_query_counts >= 2) & (session_query_counts < self.MIN_COMPLEX_QUERIES)
        ].index)

        print(f"[AOL] Complex sessions (3+ queries): {len(complex_sids):,}")
        print(f"[AOL] Simple sessions (2 queries): {len(simple_sids):,}")

        # Estimate sessions needed: target_labels / avg_events_per_session
        # Complex sessions average ~15 events, simple ~6
        estimated_sessions = self.target_labels // 8 + 1000
        if self.max_sessions:
            estimated_sessions = min(estimated_sessions, self.max_sessions)

        # Prioritise complex sessions, then fill with simple ones
        selected_sids = []
        complex_list = sorted(complex_sids)
        simple_list = sorted(simple_sids)

        # Take all complex sessions first (up to limit)
        selected_sids.extend(complex_list[:estimated_sessions])

        # Fill remaining with simple sessions
        remaining = estimated_sessions - len(selected_sids)
        if remaining > 0:
            selected_sids.extend(simple_list[:remaining])

        selected_set = set(selected_sids)
        data_df = data_df[data_df["session_id"].isin(selected_set)]

        print(f"[AOL] Building sessions from {len(data_df):,} events across {len(selected_set):,} sessions...")

        # Build session dicts with proper deduplication
        sessions = []
        for sid, group in tqdm(data_df.groupby("session_id"), desc="[AOL] Sessions", unit="sess"):
            events = self._build_session_events(sid, group)
            if len(events) >= 3:
                sessions.append({
                    "session_id": str(sid),
                    "events": events,
                })

        print(f"[AOL] Loaded {len(sessions):,} sessions with {sum(len(s['events']) for s in sessions):,} total events")
        return sessions

    def _build_session_events(self, session_id: str, group: pd.DataFrame) -> List[Dict[str, Any]]:
        """Build deduplicated, chronologically ordered events for a session.

        Each unique QueryIndex produces exactly ONE QUERY event and ONE SERP_VIEW event.
        Each clicked document produces ONE CLICK event under its query.
        """
        # Sort by timestamp
        group = group.sort_values("QueryTime")

        events = []
        seen_queries = set()

        for _, row in group.iterrows():
            query_idx = row["QueryIndex"]
            query_text = str(row["Query"]) if pd.notna(row["Query"]) else ""
            timestamp = str(row["QueryTime"])

            # Only create QUERY and SERP_VIEW once per unique QueryIndex
            if query_idx not in seen_queries:
                seen_queries.add(query_idx)

                # Determine if this query is a reformulation of a previous query
                # (used by the event_id prefix for context)
                query_num = len(seen_queries)

                # QUERY event
                events.append({
                    "event_id": f"{session_id}_qq-{query_num}",
                    "timestamp": timestamp,
                    "action_type": "QUERY",
                    "content": query_text,
                })

                # SERP_VIEW event
                if pd.notna(row.get("CandiList")) and str(row["CandiList"]).strip():
                    events.append({
                        "event_id": f"{session_id}_qq-{query_num}_serp",
                        "timestamp": timestamp,
                        "action_type": "SERP_VIEW",
                        "content": f"Search results for: {query_text}",
                    })

            # CLICK event (always unique per DocIndex)
            if pd.notna(row.get("DocIndex")) and str(row["DocIndex"]).strip():
                title = str(row["Title"]) if pd.notna(row.get("Title")) else ""
                url = str(row["Url"]) if pd.notna(row.get("Url")) else ""
                doc_idx = str(row["DocIndex"])
                events.append({
                    "event_id": f"{session_id}_qq-{len(seen_queries)}_cd-{doc_idx}",
                    "timestamp": timestamp,
                    "action_type": "CLICK",
                    "content": title or url or f"Document {doc_idx}",
                })

        return events
