"""Sliding-window rate limiter protecting gateway and network equipment from bursts."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter per client key."""

    def __init__(self, max_requests: int = 120, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, key: str) -> None:
        """Check whether key has exceeded allowed rate limit.

        Raises HTTPException(429) if exceeded.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean timestamps older than window
        timestamps = [ts for ts in self._history[key] if ts > cutoff]
        self._history[key] = timestamps

        if len(timestamps) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded. Maximum {self.max_requests} requests "
                    f"per {self.window_seconds}s. Please retry in {retry_after}s."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        self._history[key].append(now)


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=60)


async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency checking client rate limit."""
    # Use client IP or token as the rate limit key
    client_ip = request.client.host if request.client else "127.0.0.1"
    token = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    key = f"{client_ip}:{token}" if token else client_ip

    rate_limiter.check_rate_limit(key)
