"""
Redis Client Singleton
Provides persistent caching across server restarts.
"""

import redis
from typing import Optional, Any
import json
from src.settings import DEBUG_MODE
import os

# Redis Configuration
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) if os.getenv("REDIS_PASSWORD") else None

_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client singleton.
    Returns None if Redis is disabled or connection fails.
    """
    global _redis_client
    
    if not REDIS_ENABLED:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            _redis_client.ping()
            if DEBUG_MODE:
                print(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT} (DB: {REDIS_DB})")
        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ Redis connection failed: {e}. Running without Redis cache.")
            _redis_client = None
    
    return _redis_client

def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """
    Set cache with TTL in seconds.
    Returns True if successful, False otherwise.
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        serialized = json.dumps(value)
        client.setex(key, ttl, serialized)
        if DEBUG_MODE:
            print(f"📦 Redis SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Redis set error: {e}")
        return False

def get_cache(key: str) -> Optional[Any]:
    """
    Get cached value by key.
    Returns None if key doesn't exist or Redis is unavailable.
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            if DEBUG_MODE:
                print(f"✅ Redis GET: {key}")
            return json.loads(value)
        return None
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Redis get error: {e}")
        return None

def delete_cache(key: str) -> bool:
    """Delete a single cache key."""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        result = client.delete(key)
        if DEBUG_MODE and result:
            print(f"🗑️ Redis DELETE: {key}")
        return bool(result)
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Redis delete error: {e}")
        return False

def clear_cache_pattern(pattern: str) -> int:
    """
    Clear all keys matching pattern (e.g., 'router:*')
    Returns number of keys deleted.
    """
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = list(client.scan_iter(match=pattern))
        if keys:
            deleted = client.delete(*keys)
            if DEBUG_MODE:
                print(f"🗑️ Redis CLEAR: {deleted} keys matching '{pattern}'")
            return deleted
        return 0
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Redis clear error: {e}")
        return 0

def get_cache_stats() -> dict:
    """Get Redis cache statistics."""
    client = get_redis_client()
    if not client:
        return {"enabled": False}
    
    try:
        info = client.info("stats")
        return {
            "enabled": True,
            "total_keys": client.dbsize(),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) * 100
        }
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Redis stats error: {e}")
        return {"enabled": True, "error": str(e)}
