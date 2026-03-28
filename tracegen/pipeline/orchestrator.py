"""Per-dataset annotation orchestrator with adaptive pipeline."""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from tracegen.config import TracGenConfig
from tracegen.llm.client import LLMClient
from tracegen.llm.agents import DomainAnalystAgent, DomainCriticAgent, DomainJudgeAgent
from tracegen.pipeline.checkpoint import CheckpointManager
from tracegen.pipeline.csv_writer import CSVWriter
from tracegen.sanity.balance_monitor import BalanceMonitor
from tracegen.schemas.base import DomainSchema


class DatasetOrchestrator:
    """Orchestrates annotation for a single dataset."""

    def __init__(
        self,
        dataset_name: str,
        config: TracGenConfig,
        schema: DomainSchema,
        sessions: List[Dict[str, Any]],
        progress_queue=None,
    ):
        self.dataset_name = dataset_name
        self.config = config
        self.schema = schema
        self.sessions = sessions
        self.progress_queue = progress_queue

        # Components
        self.checkpoint_mgr = CheckpointManager(config, dataset_name)
        self.csv_writer = CSVWriter(config, dataset_name)
        self.balance_monitor = BalanceMonitor(
            dataset_name, alert_threshold=config.balance_alert_threshold
        )

        # LLM setup
        self.client = LLMClient(config)
        self.analyst = DomainAnalystAgent(self.client, schema, config)
        self.critic = DomainCriticAgent(self.client, schema, config)
        self.judge = DomainJudgeAgent(self.client, schema, config)

        # State
        self._stop_requested = False
        self._start_time: Optional[float] = None
        self._sessions_completed = 0
        self._total_events_annotated = 0

    def run(self):
        """Main entry point — runs the async event loop."""
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            print(f"\n[{self.dataset_name}] Interrupted. Saving checkpoint...")
            self.checkpoint_mgr.force_save()

    async def _run_async(self):
        """Async orchestration loop."""
        self._start_time = time.time()

        # Register signal handler on the event loop for clean async cancellation
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(
                __import__("signal").SIGINT,
                self._async_stop,
            )
        except NotImplementedError:
            pass  # Windows doesn't support add_signal_handler

        # Load checkpoint
        completed_ids = self.checkpoint_mgr.load()
        remaining = [s for s in self.sessions if s["session_id"] not in completed_ids]
        total = len(self.sessions)
        self._sessions_completed = len(completed_ids)

        print(
            f"[{self.dataset_name}] Starting: {len(remaining):,} sessions remaining "
            f"({self._sessions_completed:,}/{total:,} already done)"
        )

        # Process in batches
        batch_size = self.config.max_concurrent_sessions
        try:
            for batch_start in range(0, len(remaining), batch_size):
                if self._stop_requested:
                    print(f"\n[{self.dataset_name}] Stop requested. Saving checkpoint...")
                    break

                batch = remaining[batch_start: batch_start + batch_size]

                # Process batch concurrently
                tasks = [asyncio.create_task(self._annotate_session(s)) for s in batch]
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    # Cancel remaining tasks in the batch
                    for t in tasks:
                        t.cancel()
                    print(f"\n[{self.dataset_name}] Batch cancelled. Saving checkpoint...")
                    break

                for session, result in zip(batch, results):
                    if isinstance(result, (Exception, asyncio.CancelledError)):
                        error_msg = str(result)[:500]
                        self.checkpoint_mgr.record_error(session["session_id"], error_msg)
                        if self.config.verbose:
                            print(f"[{self.dataset_name}] Error on {session['session_id']}: {error_msg}")
                        continue

                    # Write results
                    self.csv_writer.append(result)

                    # Update monitoring
                    events = result.get("annotated_events", [])
                    labels = [e.get("cognitive_label", "") for e in events]
                    self.balance_monitor.update_from_labels(labels)
                    label_counts = {}
                    for lb in labels:
                        label_counts[lb] = label_counts.get(lb, 0) + 1

                    self.checkpoint_mgr.mark_complete(session["session_id"], label_counts)
                    self._sessions_completed += 1
                    self._total_events_annotated += len(events)

                # Report progress
                self._report_progress(total)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print(f"\n[{self.dataset_name}] Interrupted during processing.")

        # Final save
        self.checkpoint_mgr.force_save()

        elapsed = time.time() - self._start_time
        print(
            f"\n[{self.dataset_name}] Done: {self._sessions_completed:,} sessions, "
            f"{self._total_events_annotated:,} events in {elapsed / 60:.1f} min"
        )
        print(f"[{self.dataset_name}] Labels: {self.balance_monitor.summary_line()}")
        print(f"[{self.dataset_name}] Errors: {self.checkpoint_mgr.error_count}")
        print(f"[{self.dataset_name}] Output: {self.csv_writer.path}")

    def _async_stop(self):
        """Called from the event loop's signal handler — sets stop flag."""
        self._stop_requested = True
        # Cancel all running tasks in the current event loop
        loop = asyncio.get_running_loop()
        for task in asyncio.all_tasks(loop):
            if task is not asyncio.current_task():
                task.cancel()

    async def _annotate_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Annotate a single session using the configured pipeline mode."""
        session_id = session["session_id"]
        events = session["events"]

        # Step 1: Always run Analyst
        analyst_result = await self.analyst.analyze(events)

        # Determine pipeline path
        if self.config.pipeline_mode == "single":
            return self._build_analyst_only_result(session_id, events, analyst_result)

        if self.config.pipeline_mode == "adaptive":
            min_confidence = min(
                d.get("confidence", 0.0) for d in analyst_result["decisions"]
            )
            if min_confidence >= self.config.confidence_threshold:
                return self._build_analyst_only_result(session_id, events, analyst_result)

        # Step 2: Critic review
        critic_result = await self.critic.review(events, analyst_result["decisions"])

        # Step 3: Judge decision
        judge_result = await self.judge.decide(
            events, analyst_result["decisions"], critic_result["decisions"]
        )

        return self._build_full_result(
            session_id, events, analyst_result, critic_result, judge_result
        )

    def _build_analyst_only_result(
        self,
        session_id: str,
        events: List[Dict],
        analyst_result: Dict,
    ) -> Dict[str, Any]:
        """Build result using only analyst labels (single/adaptive-confident path)."""
        annotated = []
        for event, decision in zip(events, analyst_result["decisions"]):
            annotated.append({
                "session_id": session_id,
                "event_id": event.get("event_id", ""),
                "timestamp": event.get("timestamp", ""),
                "action_type": event.get("action_type", ""),
                "content": event.get("content", ""),
                "cognitive_label": decision.get("label", ""),
                "analyst_label": decision.get("label", ""),
                "analyst_justification": decision.get("justification", ""),
                "critic_label": "",
                "critic_agreement": "",
                "critic_justification": "",
                "judge_justification": "",
                "confidence_score": decision.get("confidence", 0.0),
                "disagreement_score": 0.0,
                "flagged_for_review": False,
            })
        return {
            "session_id": session_id,
            "annotated_events": annotated,
            "pipeline_mode": "analyst_only",
        }

    def _build_full_result(
        self,
        session_id: str,
        events: List[Dict],
        analyst_result: Dict,
        critic_result: Dict,
        judge_result: Dict,
    ) -> Dict[str, Any]:
        """Build result from full 3-agent pipeline."""
        analyst_decs = analyst_result["decisions"]
        critic_decs = critic_result["decisions"]
        judge_decs = judge_result["decisions"]

        annotated = []
        for i, event in enumerate(events):
            a = analyst_decs[i] if i < len(analyst_decs) else {}
            c = critic_decs[i] if i < len(critic_decs) else {}
            j = judge_decs[i] if i < len(judge_decs) else {}

            # Compute disagreement (simple: label match)
            disagreement = 1.0 if a.get("label") != c.get("label") else 0.0

            annotated.append({
                "session_id": session_id,
                "event_id": event.get("event_id", ""),
                "timestamp": event.get("timestamp", ""),
                "action_type": event.get("action_type", ""),
                "content": event.get("content", ""),
                "cognitive_label": j.get("final_label", c.get("label", a.get("label", ""))),
                "analyst_label": a.get("label", ""),
                "analyst_justification": a.get("justification", ""),
                "critic_label": c.get("label", ""),
                "critic_agreement": c.get("agreement", ""),
                "critic_justification": c.get("justification", ""),
                "judge_justification": j.get("justification", ""),
                "confidence_score": j.get("confidence", 0.0),
                "disagreement_score": disagreement,
                "flagged_for_review": j.get("flag_for_review", disagreement > 0.5),
            })

        return {
            "session_id": session_id,
            "annotated_events": annotated,
            "pipeline_mode": "full",
        }

    def _report_progress(self, total: int):
        """Report progress to queue (for parent process) and stdout."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        rate = self._sessions_completed / max(elapsed / 60, 0.01)

        remaining = total - self._sessions_completed
        eta_min = remaining / max(rate, 0.01)

        status = {
            "dataset": self.dataset_name,
            "completed": self._sessions_completed,
            "total": total,
            "events_annotated": self._total_events_annotated,
            "rate_per_min": round(rate, 1),
            "eta_minutes": round(eta_min, 1),
            "errors": self.checkpoint_mgr.error_count,
            "labels": self.balance_monitor.summary_line(),
            "distribution": self.balance_monitor.get_counts(),
        }

        if self.progress_queue:
            self.progress_queue.put(status)
        else:
            pct = self._sessions_completed / max(total, 1) * 100
            print(
                f"[{self.dataset_name}] {pct:.0f}% "
                f"({self._sessions_completed:,}/{total:,}) "
                f"| {rate:.1f} sess/min | ETA: {eta_min:.0f}m "
                f"| {self.balance_monitor.summary_line()}"
            )
