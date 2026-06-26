"""
Production-ready async cache utilities with Redis support and in-memory fallback.

Why this exists:
----------------
AI applications often perform expensive, high-latency LLM calls.
Caching identical prompts reduces OpenAI API costs and latency.
This utility provides an asynchronous, distributed-safe caching layer
using Redis, falling back gracefully to a thread-safe in-memory cache
if Redis is unavailable (e.g., during local development without Docker).
"""

import hashlib
import json
import threading
from typing import Any, Optional
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logger import logger


class SmartCache:
    """
    Async cache with Redis backend and thread-safe in-memory fallback.
    """

    def __init__(self) -> None:
        self.redis_url = settings.REDIS_URL
        self.redis: Optional[aioredis.Redis] = None
        self._memory_cache: dict[str, Any] = {}
        self._memory_lock = threading.Lock()
        self._redis_connected = False
        self._initialized = False

    async def _init_redis(self) -> None:
        """
        Lazily initialize Redis connection client.
        """
        if self._initialized:
            return

        try:
            self.redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            # Test connection
            await self.redis.ping()
            self._redis_connected = True
            logger.info("cache_redis_connected", url=self.redis_url)
        except Exception as err:
            self._redis_connected = False
            logger.warning(
                "cache_redis_connection_failed",
                error=str(err),
                detail="Falling back to in-memory cache.",
            )
        self._initialized = True

    def generate_cache_key(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Generate a deterministic cache key from prompt contents.

        Args:
            system_prompt: System instruction prompt.
            user_prompt: User input prompt.

        Returns:
            SHA-256 hash string.
        """
        combined = f"{system_prompt}:{user_prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key.

        Returns:
            The parsed value from cache, or None if not found/error.
        """
        await self._init_redis()

        if self._redis_connected and self.redis:
            try:
                val = await self.redis.get(key)
                if val is not None:
                    logger.debug("cache_hit_redis", key=key)
                    return json.loads(val)
            except Exception as err:
                logger.warning("cache_get_redis_error", error=str(err))

        # Fallback to in-memory
        with self._memory_lock:
            val = self._memory_cache.get(key)
            if val is not None:
                logger.debug("cache_hit_memory", key=key)
                # Return a deep copy or loaded version to simulate serialization
                return json.loads(json.dumps(val))

        logger.debug("cache_miss", key=key)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: int = 86400,
    ) -> None:
        """
        Store a value in the cache with a TTL (expiration).

        Args:
            key: Cache key.
            value: Serializable object to cache.
            expire_seconds: Time to live in seconds (default 1 day).
        """
        await self._init_redis()
        serialized = json.dumps(value)

        if self._redis_connected and self.redis:
            try:
                await self.redis.set(
                    key,
                    serialized,
                    ex=expire_seconds,
                )
                logger.debug("cache_set_redis", key=key, expire=expire_seconds)
                return
            except Exception as err:
                logger.warning("cache_set_redis_error", error=str(err))

        # Fallback to in-memory
        with self._memory_lock:
            self._memory_cache[key] = value
            # Expiry in memory is not strictly pruned in this simple dict,
            # but is sufficient as a lightweight development fallback.
            logger.debug("cache_set_memory", key=key)

    async def delete(self, key: str) -> None:
        """
        Remove a key from cache.
        """
        await self._init_redis()

        if self._redis_connected and self.redis:
            try:
                await self.redis.delete(key)
                logger.debug("cache_delete_redis", key=key)
            except Exception as err:
                logger.warning("cache_delete_redis_error", error=str(err))

        with self._memory_lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                logger.debug("cache_delete_memory", key=key)


cache = SmartCache()