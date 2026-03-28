"""CLI interface for the cognitive trace generation pipeline."""

import argparse
import sys

from tracegen.config import load_config, discover_models, auto_assign_analyst, auto_assign_critic


def main():
    parser = argparse.ArgumentParser(
        prog="tracegen",
        description="Generate cognitive traces for AOL, StackOverflow, and MovieLens datasets",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── run ──
    run_parser = subparsers.add_parser("run", help="Generate cognitive traces")
    run_parser.add_argument(
        "--datasets", default="aol,stackoverflow,movielens",
        help="Comma-separated datasets (default: all three)",
    )
    run_parser.add_argument(
        "--mode", choices=["full", "adaptive", "single"], default="adaptive",
        help="Pipeline mode (default: adaptive)",
    )
    run_parser.add_argument("--confidence", type=float, default=0.85, help="Confidence threshold for adaptive mode")
    run_parser.add_argument("--analyst-model", default=None, help="Model for analyst role")
    run_parser.add_argument("--critic-model", default=None, help="Model for critic role")
    run_parser.add_argument("--judge-model", default=None, help="Model for judge role")
    run_parser.add_argument("--concurrent", type=int, default=5, help="Max concurrent sessions per dataset")
    run_parser.add_argument("--target-aol", type=int, default=200_000, help="Target AOL labels")
    run_parser.add_argument("--target-so", type=int, default=175_000, help="Target SO labels")
    run_parser.add_argument("--target-ml", type=int, default=125_000, help="Target ML labels")
    run_parser.add_argument("--output-dir", default=None, help="Output directory")
    run_parser.add_argument("--env-file", default=None, help="Path to .env file")
    run_parser.add_argument("--session-strategy", choices=["truncate", "sliding_window", "full"], default="sliding_window")
    run_parser.add_argument("--window-size", type=int, default=30)
    run_parser.add_argument("--temperature", type=float, default=0.3)
    run_parser.add_argument("--dry-run", action="store_true", help="Validate config and show plan")
    run_parser.add_argument("--verbose", action="store_true")
    run_parser.add_argument("--single-process", action="store_true", help="Run sequentially (no multiprocessing)")

    # ── resume ──
    resume_parser = subparsers.add_parser("resume", help="Resume interrupted generation")
    resume_parser.add_argument("--datasets", default=None, help="Datasets to resume (default: all with checkpoints)")
    resume_parser.add_argument("--env-file", default=None)
    resume_parser.add_argument("--output-dir", default=None)
    resume_parser.add_argument("--verbose", action="store_true")

    # ── status ──
    status_parser = subparsers.add_parser("status", help="Show checkpoint status")
    status_parser.add_argument("--env-file", default=None)
    status_parser.add_argument("--output-dir", default=None)

    # ── check ──
    check_parser = subparsers.add_parser("check", help="Run sanity checks on output")
    check_parser.add_argument("--dataset", default=None, help="Dataset to check")
    check_parser.add_argument("--file", default=None, help="Specific CSV to check")
    check_parser.add_argument("--env-file", default=None)
    check_parser.add_argument("--output-dir", default=None)

    # ── clean ──
    clean_parser = subparsers.add_parser("clean", help="Remove checkpoints to start fresh")
    clean_parser.add_argument("--dataset", default=None, help="Dataset to clean (default: all)")
    clean_parser.add_argument("--env-file", default=None)
    clean_parser.add_argument("--output-dir", default=None)
    clean_parser.add_argument("--confirm", action="store_true", help="Skip confirmation")

    # ── models ──
    models_parser = subparsers.add_parser("models", help="Discover available self-hosted models")
    models_parser.add_argument("--env-file", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "resume":
        _cmd_resume(args)
    elif args.command == "status":
        _cmd_status(args)
    elif args.command == "check":
        _cmd_check(args)
    elif args.command == "clean":
        _cmd_clean(args)
    elif args.command == "models":
        _cmd_models(args)


def _cmd_run(args):
    config = load_config(
        env_file=args.env_file,
        output_dir=args.output_dir,
        pipeline_mode=args.mode,
        confidence_threshold=args.confidence,
        analyst_model=args.analyst_model,
        critic_model=args.critic_model,
        judge_model=args.judge_model,
        max_concurrent_sessions=args.concurrent,
        aol_target=args.target_aol,
        so_target=args.target_so,
        ml_target=args.target_ml,
        session_strategy=args.session_strategy,
        window_size=args.window_size,
        temperature=args.temperature,
        verbose=args.verbose,
        datasets=args.datasets.split(","),
    )

    # Auto-discover and assign models
    available = discover_models(config)
    if available:
        print(f"[MODELS] Available self-hosted: {', '.join(available)}")

    config.analyst_model = auto_assign_analyst(config, available)
    print(f"[MODELS] Analyst: {config.analyst_model}")

    config.critic_model = auto_assign_critic(config, available)
    print(f"[MODELS] Critic:  {config.critic_model}")
    print(f"[MODELS] Judge:   {config.judge_model}")

    # Validate
    if not config.up_llm_api_key and not config.openai_api_key:
        print("[ERROR] No API keys configured. Set UP_LLM_API and/or OPEN_AI_KEY in .env")
        sys.exit(1)

    if args.dry_run:
        _print_dry_run(config)
        return

    # Run
    if args.single_process or len(config.datasets) == 1:
        from tracegen.pipeline.parallel_runner import run_single_dataset
        for ds in config.datasets:
            run_single_dataset(config, ds)
    else:
        from tracegen.pipeline.parallel_runner import ParallelRunner
        runner = ParallelRunner(config)
        runner.run()


def _cmd_resume(args):
    config = load_config(env_file=args.env_file, output_dir=args.output_dir, verbose=args.verbose)

    # Auto-discover and assign models
    available = discover_models(config)
    config.analyst_model = auto_assign_analyst(config, available)
    config.critic_model = auto_assign_critic(config, available)

    # Determine datasets with existing checkpoints
    from pathlib import Path
    checkpoint_dir = Path(config.checkpoint_dir)
    if args.datasets:
        datasets = args.datasets.split(",")
    else:
        datasets = []
        for ds in ["aol", "stackoverflow", "movielens"]:
            if (checkpoint_dir / f"{ds}_checkpoint.json").exists():
                datasets.append(ds)

    if not datasets:
        print("No checkpoints found to resume.")
        sys.exit(0)

    config.datasets = datasets
    print(f"Resuming datasets: {', '.join(datasets)}")

    from tracegen.pipeline.parallel_runner import ParallelRunner
    runner = ParallelRunner(config)
    runner.run()


def _cmd_status(args):
    config = load_config(env_file=args.env_file, output_dir=args.output_dir)
    from tracegen.monitor.progress import show_status
    show_status(config)


def _cmd_check(args):
    config = load_config(env_file=args.env_file, output_dir=args.output_dir)
    from tracegen.sanity.post_check import check_dataset
    check_dataset(config, dataset=args.dataset, file_path=args.file)


def _cmd_clean(args):
    from pathlib import Path

    config = load_config(env_file=args.env_file, output_dir=args.output_dir)
    checkpoint_dir = Path(config.checkpoint_dir)

    if args.dataset:
        targets = [checkpoint_dir / f"{args.dataset}_checkpoint.json"]
    else:
        targets = list(checkpoint_dir.glob("*_checkpoint.json"))

    if not targets:
        print("No checkpoints to clean.")
        return

    if not args.confirm:
        print("Checkpoints to remove:")
        for t in targets:
            if t.exists():
                print(f"  {t}")
        resp = input("Proceed? [y/N] ")
        if resp.lower() != "y":
            print("Cancelled.")
            return

    for t in targets:
        if t.exists():
            t.unlink()
            print(f"  Removed: {t.name}")


def _cmd_models(args):
    config = load_config(env_file=args.env_file)
    if not config.up_llm_base_url:
        print("No UP_BASE_URL configured in .env")
        return

    print(f"Discovering models at {config.up_llm_base_url}...")
    models = discover_models(config)
    if models:
        print(f"\nAvailable models ({len(models)}):")
        for m in models:
            print(f"  - {m}")
    else:
        print("No models found or endpoint unreachable.")


def _print_dry_run(config):
    print("\n" + "=" * 70)
    print("DRY RUN — Configuration Summary")
    print("=" * 70)
    print(f"  Pipeline mode:     {config.pipeline_mode}")
    print(f"  Confidence thresh: {config.confidence_threshold}")
    print(f"  Session strategy:  {config.session_strategy} (window={config.window_size})")
    print(f"  Temperature:       {config.temperature}")
    print(f"  Concurrent:        {config.max_concurrent_sessions}")
    print(f"\n  Models:")
    print(f"    Analyst: {config.analyst_model}")
    print(f"    Critic:  {config.critic_model}")
    print(f"    Judge:   {config.judge_model}")
    print(f"\n  Endpoints:")
    print(f"    Self-hosted: {config.up_llm_base_url or 'NOT SET'}")
    print(f"    OpenAI key:  {'***' + config.openai_api_key[:8] if config.openai_api_key else 'NOT SET'}")
    print(f"\n  Targets:")
    for ds in config.datasets:
        target = config.get_target(ds)
        est_sessions = target // 10  # rough estimate
        print(f"    {ds:15s} {target:>8,} labels (~{est_sessions:,} sessions)")
    print(f"\n  Output: {config.output_dir}")
    print(f"  Checkpoints: {config.checkpoint_dir}")
    print("=" * 70)
