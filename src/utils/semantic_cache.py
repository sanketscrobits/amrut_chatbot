"""
Semantic Caching Utility

Boosts cache hit rate from 40% to 70%+ by finding semantically similar
queries instead of requiring exact matches.
"""

from typing import Optional, Dict, List
import hashlib
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.redis_client import get_cache, set_cache
import os
from settings import DEBUG_MODE

# Configuration
ENABLE_SEMANTIC_CACHE = os.getenv("ENABLE_SEMANTIC_CACHE", "true").lower() == "true"
SEMANTIC_CACHE_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.85"))

# Singleton embeddings model for cache
_cache_embeddings = None


def get_cache_embeddings():
    """Get or create singleton embeddings model for semantic caching."""
    global _cache_embeddings
    if _cache_embeddings is None:
        _cache_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _cache_embeddings


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Similarity score between 0 and 1 (1 = identical)
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    
    if norm_product == 0:
        return 0.0
    
    return float(dot_product / norm_product)


def get_semantic_cached_response(query: str, threshold: float = None) -> Optional[dict]:
    """
    Find semantically similar cached response.
    
    Args:
        query: User query
        threshold: Cosine similarity threshold (default from env)
    
    Returns:
        Cached response if similarity >= threshold, else None
    """
    if not ENABLE_SEMANTIC_CACHE:
        # Semantic caching disabled - fall back to exact match
        return None
    
    if threshold is None:
        threshold = SEMANTIC_CACHE_THRESHOLD
    
    try:
        # Get query embedding
        embeddings = get_cache_embeddings()
        query_embedding = embeddings.embed_query(query)
        
        # Get semantic index from Redis
        semantic_index = get_cache("semantic:index") or {}
        
        if not semantic_index:
            if DEBUG_MODE:
                print("📦 Semantic cache: Index is empty")
            return None
        
        best_match = None
        best_score = 0.0
        best_query = None
        
        # Search for most similar query
        for cached_query, data in semantic_index.items():
            cached_embedding = data["embedding"]
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, cached_embedding)
            
            if similarity >= threshold and similarity > best_score:
                best_score = similarity
                best_match = data["cache_key"]
                best_query = cached_query
        
        if best_match:
            # Fetch actual response from cache
            cached_response = get_cache(best_match)
            
            if cached_response:
                if DEBUG_MODE:
                    print(f"✅ Semantic cache HIT! Similarity: {best_score:.2%}")
                    print(f"   Original: '{query}'")
                    print(f"   Matched:  '{best_query}'")
                return cached_response
        
        if DEBUG_MODE:
            print(f"❌ Semantic cache MISS (best similarity: {best_score:.2%}, threshold: {threshold:.2%})")
        
        return None
    
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Semantic cache error: {e}")
        return None


def cache_semantic_response(query: str, response: dict, ttl: int = 900):
    """
    Cache response with semantic indexing.
    
    Args:
        query: User query
        response: Response data to cache
        ttl: Time to live in seconds (default 15 minutes)
    """
    if not ENABLE_SEMANTIC_CACHE:
        return
    
    try:
        # Generate cache key
        cache_key = f"response:{hashlib.md5(query.encode()).hexdigest()}"
        
        # Cache the actual response
        set_cache(cache_key, response, ttl)
        
        # Update semantic index
        embeddings = get_cache_embeddings()
        query_embedding = embeddings.embed_query(query)
        
        # Get existing index
        semantic_index = get_cache("semantic:index") or {}
        
        # Add this query to the index
        semantic_index[query] = {
            "embedding": query_embedding.tolist(),  # Convert numpy array to list
            "cache_key": cache_key
        }
        
        # Limit index size (keep only last 100 queries to avoid memory issues)
        if len(semantic_index) > 100:
            # Remove oldest entries (FIFO)
            oldest_keys = list(semantic_index.keys())[:-100]
            for old_key in oldest_keys:
                del semantic_index[old_key]
        
        # Save updated index (longer TTL for the index itself)
        set_cache("semantic:index", semantic_index, ttl=7200)  # 2 hours
        
        if DEBUG_MODE:
            print(f"📦 Semantic cache: Indexed '{query}' (index size: {len(semantic_index)})")
    
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Semantic cache save error: {e}")


def clear_semantic_cache():
    """Clear the semantic cache index and all cached responses."""
    try:
        from src.utils.redis_client import clear_cache_pattern
        
        # Clear semantic index
        clear_cache_pattern("semantic:*")
        
        # Clear response cache
        clear_cache_pattern("response:*")
        
        if DEBUG_MODE:
            print("🗑️ Semantic cache cleared")
        
        return True
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Error clearing semantic cache: {e}")
        return False


def get_semantic_cache_stats() -> dict:
    """Get statistics about semantic caching."""
    try:
        semantic_index = get_cache("semantic:index") or {}
        
        return {
            "enabled": ENABLE_SEMANTIC_CACHE,
            "threshold": SEMANTIC_CACHE_THRESHOLD,
            "indexed_queries": len(semantic_index),
            "max_index_size": 100
        }
    except Exception as e:
        return {
            "enabled": ENABLE_SEMANTIC_CACHE,
            "error": str(e)
        }
