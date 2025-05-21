"""
app/memory/redis_client.py

Asynchronous Redis client for short-term memory (session state) management.
Provides methods to connect/disconnect and to set/get/clear session contexts with TTL.
"""
import os
import json
import logging

import aioredis


class RedisClient:
    """
    Wrapper around aioredis for session-based context storage.
    """
    def __init__(self):
        # Read Redis connection URL from environment, default to localhost
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None
        # Default TTL for session context in seconds (1 hour)
        self.default_ttl = int(os.getenv("REDIS_SESSION_TTL", 3600))

    async def connect(self):
        """Establish connection to Redis."""
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                )
                logging.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logging.error(f"Failed to connect to Redis: {e}")
                raise

    async def disconnect(self):
        """Close the Redis connection."""
        if self._redis:
            try:
                await self._redis.close()
                logging.info("Redis connection closed.")
            except Exception as e:
                logging.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None

    async def set_session_context(self, session_id: str, context: dict, ttl: int = None):
        """
        Store the serialized context dict for a given session_id with TTL.
        :param session_id: Unique identifier for the session.
        :param context: Dictionary representing the session state.
        :param ttl: Time-to-live in seconds; defaults to self.default_ttl.
        """
        if self._redis is None:
            raise RuntimeError("Redis connection is not established.")
        key = f"session:{session_id}"
        data = json.dumps(context)
        expire = ttl or self.default_ttl
        try:
            await self._redis.set(key, data, ex=expire)
            logging.debug(f"Set context for {key} with TTL={expire}s")
        except Exception as e:
            logging.error(f"Error setting session context for {session_id}: {e}")
            raise

    async def get_session_context(self, session_id: str) -> dict:
        """
        Retrieve and deserialize the context for a given session_id.
        Returns {} if not found or on error.
        """
        if self._redis is None:
            raise RuntimeError("Redis connection is not established.")
        key = f"session:{session_id}"
        try:
            raw = await self._redis.get(key)
            if raw:
                context = json.loads(raw)
                logging.debug(f"Retrieved context for {key}")
                return context
            else:
                logging.debug(f"No context found for {key}, returning empty dict.")
                return {}
        except Exception as e:
            logging.error(f"Error retrieving session context for {session_id}: {e}")
            return {}

    async def clear_session_context(self, session_id: str):
        """
        Delete the stored context for a given session_id.
        """
        if self._redis is None:
            raise RuntimeError("Redis connection is not established.")
        key = f"session:{session_id}"
        try:
            await self._redis.delete(key)
            logging.debug(f"Cleared context for {key}")
        except Exception as e:
            logging.warning(f"Error clearing context for {session_id}: {e}")


# Instantiate a singleton client for import
redis_client = RedisClient()
