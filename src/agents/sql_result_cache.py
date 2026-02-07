"""
SQL Query Result Caching System
Caches SQL query results in Redis to avoid repeated database hits.
"""
import hashlib
import os
from typing import Optional
from src.utils.redis_client import get_cache, set_cache

# Configuration
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_TTL_SQL = int(os.getenv("REDIS_TTL_SQL_RESULTS", "900"))  # 15 minutes default

def get_query_cache_key(user_query: str, sql_query: str) -> str:
    """
    Generate Redis cache key from user query + SQL query.
    This ensures same question with same SQL gets cached result.
    """
    # Normalize for consistent caching
    normalized_user = user_query.lower().strip()
    normalized_sql = sql_query.strip()
    
    # Create fingerprint
    combined = f"{normalized_user}|{normalized_sql}"
    hash_key = hashlib.md5(combined.encode()).hexdigest()[:16]
    
    return f"sql_result:{hash_key}"

def get_cached_sql_result(user_query: str, sql_query: str) -> Optional[str]:
    """
    Check Redis cache for previously executed SQL query result.
    
    Args:
        user_query: Original user question
        sql_query: Generated SQL query
        
    Returns:
        Cached response string if found, None otherwise
    """
    if not REDIS_ENABLED:
        return None
    
    cache_key = get_query_cache_key(user_query, sql_query)
    cached_result = get_cache(cache_key)
    
    if cached_result:
        print(f"[SQL_CACHE] ✅ HIT: Returning cached result (key: {cache_key[:12]}...)")
        return cached_result
    
    print(f"[SQL_CACHE] ❌ MISS: No cached result found")
    return None

def cache_sql_result(user_query: str, sql_query: str, result: str):
    """
    Cache SQL query result in Redis with TTL.
    
    Args:
        user_query: Original user question
        sql_query: Generated SQL query
        result: Final synthesized answer
    """
    if not REDIS_ENABLED:
        return
    
    cache_key = get_query_cache_key(user_query, sql_query)
    set_cache(cache_key, result, REDIS_TTL_SQL)
    
    print(f"[SQL_CACHE] 💾 STORED: Cached result for {REDIS_TTL_SQL}s (key: {cache_key[:12]}...)")

def clear_sql_cache():
    """Clear all SQL result caches (admin function)"""
    # This would require Redis SCAN functionality
    # For now, keys expire based on TTL
    pass
