"""OpenAI-compatible LLM client with retry support."""

import asyncio
import time
from typing import Optional, Tuple

import openai

from tracegen.config import TracGenConfig
from tracegen.llm.rate_limiter import RateLimiter


class LLMClient:
    """Unified client for self-hosted (OpenAI-compatible) and OpenAI endpoints."""

    def __init__(self, config: TracGenConfig):
        self.config = config

        # Build OpenAI clients
        self._openai_client: Optional[openai.OpenAI] = None
        self._selfhosted_client: Optional[openai.OpenAI] = None

        if config.openai_api_key:
            self._openai_client = openai.OpenAI(
                api_key=config.openai_api_key,
                timeout=config.request_timeout,
            )

        if config.up_llm_base_url and config.up_llm_api_key:
            base_url = config.up_llm_base_url.rstrip("/")
            if not base_url.endswith("/v1"):
                base_url = f"{base_url}/v1"
            self._selfhosted_client = openai.OpenAI(
                api_key=config.up_llm_api_key,
                base_url=base_url,
                timeout=config.request_timeout,
            )

        # Rate limiters per endpoint
        self._selfhosted_limiter = RateLimiter(calls_per_minute=30, burst=5)
        self._openai_limiter = RateLimiter(calls_per_minute=60, burst=10)

    def _is_selfhosted_model(self, model: str) -> bool:
        """Check if a model should use the self-hosted endpoint."""
        openai_models = {"gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini"}
        return model not in openai_models

    async def generate(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        role: str = "analyst",
    ) -> Tuple[str, float]:
        """Generate a completion. Returns (response_text, elapsed_seconds).

        Retries on transient errors. Raises on persistent failures.
        """
        temp = temperature if temperature is not None else self.config.temperature

        last_error = None
        for attempt in range(1, self.config.max_retries + 2):  # +1 for initial attempt
            try:
                text, elapsed = await self._call(model, prompt, max_tokens, temp)
                return text, elapsed
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_error = e
                if attempt <= self.config.max_retries:
                    wait = 2 ** attempt
                    if self.config.verbose:
                        print(f"[RETRY] {model} attempt {attempt} failed: {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"LLM call to '{model}' failed after {self.config.max_retries + 1} attempts: {last_error}"
        ) from last_error

    async def _call(
        self, model: str, prompt: str, max_tokens: int, temperature: float
    ) -> Tuple[str, float]:
        """Execute a single LLM call through the appropriate client."""
        is_selfhosted = self._is_selfhosted_model(model)
        client = self._selfhosted_client if is_selfhosted else self._openai_client
        limiter = self._selfhosted_limiter if is_selfhosted else self._openai_limiter

        if client is None:
            endpoint = "self-hosted" if is_selfhosted else "OpenAI"
            raise ValueError(f"No {endpoint} client configured. Check your .env file.")

        async with limiter:
            start = time.time()
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
                timeout=self.config.request_timeout + 30,  # hard cap above httpx timeout
            )
            elapsed = time.time() - start

        text = response.choices[0].message.content
        if not text:
            raise ValueError(f"Empty response from {model}")
        return text, elapsed
