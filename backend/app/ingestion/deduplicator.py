"""Deduplicates articles using URL hashes stored in Redis."""
import hashlib
import logging

import redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None
DEDUP_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def _url_key(url: str) -> str:
    digest = hashlib.sha256(url.encode()).hexdigest()
    return f"seen:url:{digest}"


def is_seen(url: str) -> bool:
    """Return True if we have already processed this URL."""
    try:
        return bool(_get_redis().exists(_url_key(url)))
    except redis.RedisError as e:
        logger.warning("Redis error checking dedup for %s: %s", url, e)
        return False


def mark_seen(url: str) -> None:
    """Mark a URL as processed with a 7-day expiry."""
    try:
        _get_redis().setex(_url_key(url), DEDUP_TTL_SECONDS, "1")
    except redis.RedisError as e:
        logger.warning("Redis error marking seen for %s: %s", url, e)
