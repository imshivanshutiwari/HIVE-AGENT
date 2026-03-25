"""GitHub API and Claude API rate limit management."""
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    remaining: int
    reset_at: float
    limit: int


class RateLimiter:
    """Token-bucket rate limiter for GitHub and Claude APIs."""

    def __init__(self, github_rpm: int = 30, claude_rpm: int = 50):
        self.limits = {
            "github": github_rpm,
            "claude": claude_rpm,
        }
        self.calls: Dict[str, list] = {"github": [], "claude": []}
        self.locks: Dict[str, Lock] = {"github": Lock(), "claude": Lock()}

    def acquire(self, api: str = "github") -> None:
        limit = self.limits.get(api, 30)
        with self.locks[api]:
            now = time.time()
            # Remove calls older than 60 seconds
            self.calls[api] = [t for t in self.calls[api] if now - t < 60]
            if len(self.calls[api]) >= limit:
                oldest = self.calls[api][0]
                sleep_time = 60 - (now - oldest) + 0.1
                logger.info(f"Rate limit for {api}: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                now = time.time()
                self.calls[api] = [t for t in self.calls[api] if now - t < 60]
            self.calls[api].append(time.time())

    def get_status(self) -> Dict[str, Dict[str, int]]:
        now = time.time()
        return {
            api: {
                "used_last_minute": len([t for t in self.calls[api] if now - t < 60]),
                "limit_per_minute": self.limits[api],
            }
            for api in self.limits
        }
