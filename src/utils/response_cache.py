"""
Response Caching System
Caches full chatbot responses to avoid recomputation.
"""

from src.utils.redis_client import get_cache, set_cache
import hashlib
import os
from settings import DEBUG_MODE

# Configuration
REDIS_TTL_RESPONSE = int(os.getenv("REDIS_TTL_RESPONSE", "900"))  # 15 minutes
ENABLE_RESPONSE_CACHE = os.getenv("ENABLE_RESPONSE_CACHE", "true").lower() == "true"

def get_response_cache_key(query: str) -> str:
    """Generate cache key for full response."""
    normalized = query.lower().strip()
    # Use MD5 hash for compact keys
    hash_digest = hashlib.md5(normalized.encode()).hexdigest()[:16]
    return f"response:{hash_digest}"

def get_cached_response(query: str) -> dict | None:
    """
    Get cached full response if available.
    Returns None if cache miss or caching disabled.
    """
    if not ENABLE_RESPONSE_CACHE:
        return None
    
    cache_key = get_response_cache_key(query)
    cached = get_cache(cache_key)
    
    if cached and DEBUG_MODE:
        print(f"✅ Response Cache HIT: {query[:50]}...")
    
    return cached

def cache_response(query: str, response: dict):
    """
    Cache full chatbot response.
    TTL defaults to 15 minutes.
    """
    if not ENABLE_RESPONSE_CACHE:
        return
    
    cache_key = get_response_cache_key(query)
    success = set_cache(cache_key, response, REDIS_TTL_RESPONSE)
    
    if success and DEBUG_MODE:
        print(f"📦 Response Cached: {query[:50]}... (TTL: {REDIS_TTL_RESPONSE}s)")

def clear_response_cache():
    """Clear all cached responses."""
    from src.utils.redis_client import clear_cache_pattern
    return clear_cache_pattern("response:*")
