"""Multiprocessing coordinator for running 3 datasets in parallel."""

import multiprocessing
import signal
import time
from typing import Any, Dict, List, Optional

from tracegen.config import TracGenConfig
from tracegen.schemas import SCHEMA_REGISTRY
from tracegen.loaders import LOADER_REGISTRY
from tracegen.pipeline.orchestrator import DatasetOrchestrator


def _run_dataset_process(
    dataset_name: str,
    config: TracGenConfig,
    progress_queue: multiprocessing.Queue,
):
    """Entry point for each dataset subprocess."""
    # Get the schema and loader classes
    schema_cls = SCHEMA_REGISTRY[dataset_name]
    loader_cls = LOADER_REGISTRY[dataset_name]

    schema = schema_cls()
    target = config.get_target(dataset_name)

    # Load sessions
    loader_kwargs = {"target_labels": target}
    loader = loader_cls(**loader_kwargs)
    sessions = loader.load_sessions()

    # Run orchestrator
    orchestrator = DatasetOrchestrator(
        dataset_name=dataset_name,
        config=config,
        schema=schema,
        sessions=sessions,
        progress_queue=progress_queue,
    )
    orchestrator.run()


class ParallelRunner:
    """Coordinates parallel execution of dataset annotation."""

    def __init__(self, config: TracGenConfig):
        self.config = config
        self.progress_queue: multiprocessing.Queue = multiprocessing.Queue()
        self.processes: Dict[str, multiprocessing.Process] = {}
        self._stop_requested = False

    def run(self):
        """Launch dataset processes and monitor progress."""
        # Handle SIGINT gracefully in main process
        original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._signal_handler)

        print("=" * 70)
        print(f"Cognitive Trace Generation — {len(self.config.datasets)} datasets in parallel")
        print(f"Pipeline mode: {self.config.pipeline_mode}")
        print(f"Models: analyst={self.config.analyst_model} | critic={self.config.critic_model} | judge={self.config.judge_model}")
        print(f"Output: {self.config.output_dir}")
        print("=" * 70)

        # Launch processes
        for dataset in self.config.datasets:
            if dataset not in SCHEMA_REGISTRY:
                print(f"[WARN] Unknown dataset: {dataset}. Skipping.")
                continue

            p = multiprocessing.Process(
                target=_run_dataset_process,
                args=(dataset, self.config, self.progress_queue),
                name=f"tracegen-{dataset}",
                daemon=False,
            )
            self.processes[dataset] = p
            p.start()
            print(f"[MAIN] Started process for {dataset} (PID: {p.pid})")

        # Monitor until all done
        self._monitor()

        # Restore signal handler
        signal.signal(signal.SIGINT, original_handler)

    def _signal_handler(self, signum, frame):
        if self._stop_requested:
            # Second interrupt — force kill
            print("\n[MAIN] Force stopping all processes...")
            for p in self.processes.values():
                if p.is_alive():
                    p.terminate()
            raise KeyboardInterrupt
        else:
            self._stop_requested = True
            print("\n[MAIN] Graceful shutdown requested. Waiting for processes to save checkpoints...")
            # Processes will catch SIGINT themselves via their own signal handlers

    def _monitor(self):
        """Monitor progress from all running processes."""
        latest_status: Dict[str, Dict] = {}

        while True:
            # Check if all processes are done
            all_done = all(not p.is_alive() for p in self.processes.values())
            if all_done:
                # Drain remaining messages
                self._drain_queue(latest_status)
                break

            # Read progress messages (non-blocking with timeout)
            try:
                while True:
                    status = self.progress_queue.get(timeout=0.5)
                    latest_status[status["dataset"]] = status
            except Exception:
                pass

            # Print summary periodically
            if latest_status:
                self._print_summary(latest_status)

            time.sleep(5)

        # Final summary
        print("\n" + "=" * 70)
        print("FINAL STATUS")
        print("=" * 70)
        for dataset, p in self.processes.items():
            exit_code = p.exitcode
            status_str = "OK" if exit_code == 0 else f"Exit code {exit_code}"
            info = latest_status.get(dataset, {})
            completed = info.get("completed", "?")
            total = info.get("total", "?")
            events = info.get("events_annotated", "?")
            labels = info.get("labels", "")
            print(f"  {dataset:15s} [{status_str}] {completed}/{total} sessions, {events} events | {labels}")

        print("=" * 70)

    def _drain_queue(self, latest_status: Dict):
        try:
            while True:
                status = self.progress_queue.get_nowait()
                latest_status[status["dataset"]] = status
        except Exception:
            pass

    def _print_summary(self, latest_status: Dict[str, Dict]):
        total_completed = sum(s.get("completed", 0) for s in latest_status.values())
        total_all = sum(s.get("total", 0) for s in latest_status.values())
        total_events = sum(s.get("events_annotated", 0) for s in latest_status.values())

        parts = []
        for ds in sorted(latest_status.keys()):
            s = latest_status[ds]
            pct = s.get("completed", 0) / max(s.get("total", 1), 1) * 100
            parts.append(f"{ds}: {pct:.0f}%")

        print(
            f"  [{' | '.join(parts)}] "
            f"Total: {total_completed:,}/{total_all:,} sessions, "
            f"{total_events:,} events"
        )


def run_single_dataset(config: TracGenConfig, dataset: str):
    """Run annotation for a single dataset without multiprocessing (useful for debugging)."""
    schema_cls = SCHEMA_REGISTRY[dataset]
    loader_cls = LOADER_REGISTRY[dataset]

    schema = schema_cls()
    target = config.get_target(dataset)
    loader = loader_cls(target_labels=target)
    sessions = loader.load_sessions()

    orchestrator = DatasetOrchestrator(
        dataset_name=dataset,
        config=config,
        schema=schema,
        sessions=sessions,
    )
    orchestrator.run()
