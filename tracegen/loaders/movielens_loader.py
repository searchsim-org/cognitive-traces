"""MovieLens dataset loader — builds user-level rating sessions."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from tqdm import tqdm


class MovieLensLoader:
    """Load MovieLens ratings and build user-level sessions."""

    def __init__(
        self,
        data_dir: Optional[str] = None,
        max_sessions: Optional[int] = None,
        target_labels: int = 125_000,
        min_events: int = 5,
        max_events: int = 50,
        session_gap_hours: int = 24,
    ):
        if data_dir is None:
            data_dir = str(Path(__file__).resolve().parent.parent.parent / "builder" / "data" / "movielens")
        self.data_dir = Path(data_dir)
        self.max_sessions = max_sessions
        self.target_labels = target_labels
        self.min_events = min_events
        self.max_events = max_events
        self.session_gap_hours = session_gap_hours

    def load_sessions(self) -> List[Dict[str, Any]]:
        """Load ratings + belief data and build user sessions."""
        print("[ML] Loading MovieLens data...")

        # Load movies for title lookup
        movies_path = self.data_dir / "movies.csv"
        movies_df = pd.read_csv(movies_path)
        movie_lookup = dict(zip(movies_df["movieId"], movies_df.apply(
            lambda r: {"title": r["title"], "genres": r["genres"]}, axis=1
        )))
        print(f"[ML] Loaded {len(movie_lookup):,} movies")

        # Load ratings
        ratings_path = self.data_dir / "user_rating_history.csv"
        if not ratings_path.exists():
            raise FileNotFoundError(f"Ratings file not found: {ratings_path}")

        ratings_df = pd.read_csv(ratings_path)
        print(f"[ML] Loaded {len(ratings_df):,} ratings from {ratings_df['userId'].nunique():,} users")

        # Load belief data if available (for system predictions)
        belief_path = self.data_dir / "belief_data.csv"
        belief_lookup = {}
        if belief_path.exists():
            belief_df = pd.read_csv(belief_path)
            # Build lookup: (userId, movieId) -> belief info
            for _, row in belief_df.iterrows():
                key = (int(row.get("userId", 0)), int(row.get("movieId", 0)))
                belief_lookup[key] = {
                    "systemPredictRating": row.get("systemPredictRating"),
                    "userPredictRating": row.get("userPredictRating"),
                    "userCertainty": row.get("userCertainty"),
                    "isSeen": row.get("isSeen"),
                }
            print(f"[ML] Loaded {len(belief_lookup):,} belief records")

        # Sort by user and timestamp
        ratings_df = ratings_df.sort_values(["userId", "tstamp"]).reset_index(drop=True)
        ratings_df["datetime"] = pd.to_datetime(ratings_df["tstamp"])

        # Sessionize by user + time gap
        print("[ML] Building user sessions...")
        sessions = []
        session_gap = pd.Timedelta(hours=self.session_gap_hours)

        for user_id, user_group in tqdm(
            ratings_df.groupby("userId"), desc="[ML] Users", unit="user"
        ):
            user_events = []
            last_ts = None
            session_counter = 0

            for _, row in user_group.iterrows():
                current_ts = row["datetime"]

                # Start new session on time gap
                if last_ts is not None and (current_ts - last_ts) > session_gap:
                    if self.min_events <= len(user_events) <= self.max_events:
                        sessions.append({
                            "session_id": f"ml_{user_id}_{session_counter}",
                            "events": user_events,
                        })
                    user_events = []
                    session_counter += 1

                # Build event content
                movie_id = int(row["movieId"])
                movie_info = movie_lookup.get(movie_id, {"title": f"Movie {movie_id}", "genres": ""})
                rating = float(row["rating"])

                content_data = {
                    "movie_id": movie_id,
                    "movie_title": movie_info["title"],
                    "genres": movie_info["genres"],
                    "rating": rating,
                }

                # Add belief info if available
                belief = belief_lookup.get((int(user_id), movie_id))
                if belief:
                    sys_pred = belief.get("systemPredictRating")
                    if pd.notna(sys_pred):
                        content_data["system_rating"] = float(sys_pred)

                # Determine action type
                action_type = "RATE"
                if belief:
                    is_seen = belief.get("isSeen")
                    if is_seen == 0:
                        action_type = "BELIEF_PREDICT"
                    elif is_seen == 1 and pd.notna(belief.get("userPredictRating")) and belief["userPredictRating"] != -1:
                        action_type = "BELIEF_ELICIT"

                user_events.append({
                    "event_id": f"ml_{user_id}_{movie_id}_{row['tstamp']}",
                    "timestamp": current_ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "action_type": action_type,
                    "content": json.dumps(content_data),
                })

                last_ts = current_ts

            # Last session for this user
            if self.min_events <= len(user_events) <= self.max_events:
                sessions.append({
                    "session_id": f"ml_{user_id}_{session_counter}",
                    "events": user_events,
                })

            # Early exit if we have enough
            estimated_sessions = self.max_sessions or (self.target_labels // 12 + 500)
            if len(sessions) >= estimated_sessions:
                break

        print(f"[ML] Built {len(sessions):,} sessions with {sum(len(s['events']) for s in sessions):,} total events")
        return sessions
