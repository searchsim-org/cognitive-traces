"""Rate limiter for LLM API calls using asyncio primitives."""

import asyncio
import time


class RateLimiter:
    """Token-bucket rate limiter with burst support."""

    def __init__(self, calls_per_minute: int = 60, burst: int = 10):
        self._semaphore = asyncio.Semaphore(burst)
        self._min_interval = 60.0 / max(calls_per_minute, 1)
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a call slot is available."""
        await self._semaphore.acquire()
        async with self._lock:
            now = time.monotonic()
            wait = max(0.0, self._min_interval - (now - self._last_call))
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()

    def release(self):
        self._semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *exc):
        self.release()
