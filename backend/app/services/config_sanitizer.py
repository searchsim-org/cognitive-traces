"""Strip API keys and other secrets before persisting LLM configs."""

import re

SECRET_FIELDS: frozenset[str] = frozenset(
    {"anthropic_api_key", "openai_api_key", "google_api_key", "mistral_api_key", "ollama_base_url"}
)

SECRET_PATTERN = re.compile(r"(api[_-]?key|secret|token|password)$", re.IGNORECASE)


def strip_secrets(config):
    """Recursively drop any field whose name is a known secret or matches the pattern."""
    if isinstance(config, dict):
        return {
            k: strip_secrets(v)
            for k, v in config.items()
            if k not in SECRET_FIELDS and not SECRET_PATTERN.search(k or "")
        }
    if isinstance(config, list):
        return [strip_secrets(x) for x in config]
    return config
