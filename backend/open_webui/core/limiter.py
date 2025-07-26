import os
import logging
from datetime import datetime, timedelta
from typing import Literal, Optional

import redis.asyncio as redis

# Setup logger
log = logging.getLogger(__name__)

# Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TIMEZONE = os.getenv("LIMITER_TZ", "UTC")  # Use "Asia/Yangon" if needed


Window = Literal["day", "week", "month", "3h", "12h"]
WINDOW_SECONDS: dict[Window, int] = {
    "3h": 3 * 3600,
    "12h": 12 * 3600,
    "day": 24 * 3600,
    "week": 7 * 24 * 3600,
    "month": 30 * 24 * 3600,
}


class RateLimiter:
    def __init__(self, redis_url: str = REDIS_URL):
        log.info(f"Connecting to Redis for rate limiter at {redis_url}")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.lua_sha: Optional[str] = None

    def _get_bucket_id(self, window: Window, now: datetime) -> str:
        if window == "day":
            return now.strftime("%Y%m%d")
        if window == "week":
            week = now.isocalendar().week
            return f"{now.year}-W{week}"
        if window == "month":
            return now.strftime("%Y%m")
        log.warning(f"Invalid window type '{window}' provided.")
        raise ValueError(f"Invalid window: {window}")

    def _get_window_seconds(self, window: Window) -> int:
        return WINDOW_SECONDS.get(window, 24 * 3600)  # default to 1 day

    async def check(self, user_id: str, resource: str, limit: int, window: Window) -> bool:
        """Implements a sliding window rate limiter using ZSET."""
        now = datetime.utcnow()
        key = f"sliding:{user_id}:{resource}:{window}"
        window_secs = self._get_window_seconds(window)
        min_score = int((now - timedelta(seconds=window_secs)).timestamp())
        now_score = int(now.timestamp())
        token = f"{user_id}:{now_score}:{os.urandom(3).hex()}"  # unique per call

        try:
            pipe = self.redis.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, min_score)
            pipe.zcard(key)
            pipe.zadd(key, {token: now_score}, nx=True)  # or drop nx if you want every hit
            pipe.expire(key, window_secs + 1)
            removed, count, added, _ = await pipe.execute()
            allowed = (count + added) <= limit
            log.info(f"[SLIDING] ALLOWED key={key} added={added} count={count + added}/{limit}")
            if allowed:
                return True
            return False
        except redis.RedisError as e:
            log.error(f"[SLIDING] Redis error: {e}. Failing closed.")
            return False

    async def get_remaining(self, user_id: str, resource: str, limit: int, window: Window) -> int:
        now = datetime.utcnow()
        key = f"sliding:{user_id}:{resource}:{window}"
        window_secs = self._get_window_seconds(window)
        min_score = int((now - timedelta(seconds=window_secs)).timestamp())
        try:
            await self.redis.zremrangebyscore(key, 0, min_score)
            used = await self.redis.zcard(key)
            return max(0, limit - used)
        except redis.RedisError as e:
            log.error(f"[SLIDING] Redis error fetching remaining for key {key}: {e}")
            return 0


# Singleton instance
limiter = RateLimiter()


async def check_rate_limit(
        user_id: str, resource: str, limit: int, window: Window
) -> bool:
    """Convenience function to access the rate limiter."""
    return await limiter.check(user_id, resource, limit, window)
