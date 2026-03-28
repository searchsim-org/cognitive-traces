"""Configuration loading and TracGenConfig dataclass."""

import os
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


@dataclass
class TracGenConfig:
    """Configuration for the trace generation pipeline."""

    # LLM endpoints
    up_llm_base_url: str = ""
    up_llm_api_key: str = ""
    openai_api_key: str = ""

    # Model assignments per role
    analyst_model: str = ""  # auto-discovered or user-specified
    critic_model: str = ""  # auto-discovered or user-specified
    judge_model: str = "gpt-4o-mini"

    # Pipeline mode
    pipeline_mode: str = "adaptive"  # "full" | "adaptive" | "single"
    confidence_threshold: float = 0.85

    # Parallelism
    datasets: List[str] = field(default_factory=lambda: ["aol", "stackoverflow", "movielens"])
    max_concurrent_sessions: int = 5

    # Session handling
    session_strategy: str = "sliding_window"  # "sliding_window" | "truncate" | "full"
    window_size: int = 30

    # Targets
    aol_target: int = 200_000
    so_target: int = 175_000
    ml_target: int = 125_000

    # Output
    output_dir: str = ""
    checkpoint_dir: str = ""

    # LLM parameters
    temperature: float = 0.3
    max_retries: int = 2
    request_timeout: float = 300.0

    # Balance monitoring
    balance_alert_threshold: float = 0.50

    # Annotation mode
    causal_annotation: bool = False  # If True, use event-by-event annotation (no future leakage)

    # Verbose
    verbose: bool = False

    @property
    def config_hash(self) -> str:
        """Hash of key config params for checkpoint validation."""
        key_params = {
            "analyst_model": self.analyst_model,
            "critic_model": self.critic_model,
            "judge_model": self.judge_model,
            "pipeline_mode": self.pipeline_mode,
            "confidence_threshold": self.confidence_threshold,
            "session_strategy": self.session_strategy,
            "window_size": self.window_size,
        }
        return hashlib.md5(json.dumps(key_params, sort_keys=True).encode()).hexdigest()[:12]

    def get_target(self, dataset: str) -> int:
        return {"aol": self.aol_target, "stackoverflow": self.so_target, "movielens": self.ml_target}[dataset]


def load_config(
    env_file: Optional[str] = None,
    output_dir: Optional[str] = None,
    **overrides,
) -> TracGenConfig:
    """Load configuration from .env file and CLI overrides."""
    project_root = Path(__file__).resolve().parent.parent

    # Load .env
    env_path = Path(env_file) if env_file else project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Resolve output directories
    if output_dir:
        out = Path(output_dir)
    else:
        out = project_root / "tracegen" / "output"

    config = TracGenConfig(
        up_llm_base_url=os.getenv("UP_BASE_URL", ""),
        up_llm_api_key=os.getenv("UP_LLM_API", ""),
        openai_api_key=os.getenv("OPEN_AI_KEY", ""),
        output_dir=str(out),
        checkpoint_dir=str(out / "checkpoints"),
    )

    # Apply CLI overrides
    for key, value in overrides.items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)

    return config


def discover_models(config: TracGenConfig) -> List[str]:
    """Call GET /v1/models on the self-hosted endpoint to discover available models."""
    import httpx

    base_url = config.up_llm_base_url.rstrip("/")
    if not base_url:
        return []

    url = f"{base_url}/v1/models"
    try:
        resp = httpx.get(
            url,
            headers={"Authorization": f"Bearer {config.up_llm_api_key}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        models = [m["id"] for m in data.get("data", [])]
        return sorted(models)
    except Exception as e:
        print(f"[WARN] Could not discover models from {url}: {e}")
        return []


def auto_assign_analyst(config: TracGenConfig, available_models: List[str]) -> str:
    """Auto-assign the analyst model from available self-hosted models.

    Prefers a DeepSeek model. Exits with error if no model can be assigned.
    """
    # Check if user specified a model via CLI
    if config.analyst_model:
        # Verify user-specified model is actually available
        if config.analyst_model in available_models:
            return config.analyst_model
        # Check if it's an OpenAI model (those don't need to be discovered)
        openai_models = {"gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini"}
        if config.analyst_model in openai_models:
            return config.analyst_model
        print(f"[ERROR] Specified analyst model '{config.analyst_model}' not found on server.")
        print(f"        Available: {', '.join(available_models) if available_models else 'none'}")
        sys.exit(1)

    # Prefer deepseek
    for m in available_models:
        if "deepseek" in m.lower():
            return m

    # Use first available self-hosted model
    if available_models:
        return available_models[0]

    print("[ERROR] No analyst model specified and no self-hosted models discovered.")
    print("        Use --analyst-model to specify a model, or check UP_BASE_URL in .env")
    sys.exit(1)


def auto_assign_critic(config: TracGenConfig, available_models: List[str]) -> str:
    """Auto-assign the critic model from available self-hosted models.

    Prefers a Qwen model. Exits with error if no model can be assigned.
    """
    openai_models = {"gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini"}

    # Check if user specified a model via CLI
    if config.critic_model:
        if config.critic_model in available_models or config.critic_model in openai_models:
            return config.critic_model
        print(f"[ERROR] Specified critic model '{config.critic_model}' not found on server.")
        print(f"        Available: {', '.join(available_models) if available_models else 'none'}")
        sys.exit(1)

    # Prefer qwen
    for m in available_models:
        if "qwen" in m.lower():
            return m

    # Use any model that differs from the analyst
    for m in available_models:
        if m != config.analyst_model:
            return m

    # Last resort: use the same as analyst (still valid — just not diverse)
    if available_models:
        return available_models[0]

    print("[ERROR] No critic model specified and no self-hosted models discovered.")
    print("        Use --critic-model to specify a model, or check UP_BASE_URL in .env")
    sys.exit(1)
