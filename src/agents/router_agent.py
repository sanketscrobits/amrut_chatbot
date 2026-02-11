from datetime import datetime, timedelta
import hashlib
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.schemas.response_schema import ResponseSchema
from src.utils.llm_singleton import get_llm
from src.utils.yaml_loader import load_prompts
from src.settings import DEBUG_MODE
from src.agents.sql_template_cache import get_sql_from_template

# REDIS INTEGRATION
from src.utils.redis_client import get_cache, set_cache

# Configuration
ROUTER_CACHE_TTL_SECONDS = 3600  # 1 hour
REDIS_TTL_ROUTER = int(os.getenv("REDIS_TTL_ROUTER", "3600"))  # 1 hour
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

# In-memory cache (fallback)
_router_cache = {}  # {query_fingerprint: {route: str, expires_at: datetime}}

def normalize_query_for_cache(query: str) -> str:
    """Normalize query for cache key generation to improve hit rate.
    'Show places in Pune' and 'List Pune places' should match.
    """
    # Remove common stop words
    stop_words = {'show', 'list', 'give', 'me', 'the', 'all', 'tell', 'what', 'are', 'is', 'a', 'an', 'about', 'of', 'in', 'at', 'for'}
    words = query.lower().strip().split()
    filtered = [w for w in words if w not in stop_words]
    
    # Sort alphabetically for order-independent matching
    filtered.sort()
    
    # Create fingerprint
    normalized = ' '.join(filtered)
    return hashlib.md5(normalized.encode()).hexdigest()[:16]

def get_cached_route(query: str) -> str | None:
    """Check cache with TTL validation. Redis first, then in-memory."""
    cache_key = normalize_query_for_cache(query)
    
    # REDIS INTEGRATION: Try Redis first (if enabled)
    if REDIS_ENABLED:
        redis_key = f"router:{cache_key}"
        cached = get_cache(redis_key)
        if cached:
            if DEBUG_MODE:
                print(f"Router cache HIT (Redis): {cached}")
            return cached
    
    # Fall back to in-memory cache
    if cache_key in _router_cache:
        cached_data = _router_cache[cache_key]
        
        # Check TTL
        if datetime.now() < cached_data['expires_at']:
            ttl_remaining = (cached_data['expires_at'] - datetime.now()).seconds
            if DEBUG_MODE:
                print(f"Router cache HIT (Memory, TTL: {ttl_remaining}s)")
            return cached_data['route']
        else:
            # Expired, remove
            del _router_cache[cache_key]
    
    return None

def cache_route(query: str, route: str):
    """Cache route with TTL. Stores in both Redis and in-memory."""
    cache_key = normalize_query_for_cache(query)
    
    # REDIS INTEGRATION: Cache in Redis (if enabled)
    if REDIS_ENABLED:
        redis_key = f"router:{cache_key}"
        set_cache(redis_key, route, REDIS_TTL_ROUTER)
    
    # Also cache in-memory for fast access
    _router_cache[cache_key] = {
        'route': route,
        'expires_at': datetime.now() + timedelta(seconds=ROUTER_CACHE_TTL_SECONDS)
    }
    
    if DEBUG_MODE:
        storage = "Redis + Memory" if REDIS_ENABLED else "Memory"
        print(f"Router cache MISS: {route} (cached in {storage})")  

def get_router_chain():
    """Create the router chain."""
    llm = get_llm(model="gemini-2.5-flash", temperature=0)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "..", "utils", "prompts.yml")
    prompts = load_prompts(prompts_path)
    
    prompt_text = prompts.get("router_agent_prompt", "")
    
    prompt = ChatPromptTemplate.from_template(prompt_text + "\n\nQUERY: {input}")
    chain = prompt | llm | StrOutputParser()
    return chain

def router_agent_node(state: ResponseSchema) -> ResponseSchema:
    """
    Classify the user query to determine the best data source.
    Uses caching to avoid repeated LLM calls for similar queries.
    """
    user_input = state["validated_user_input"]
    if DEBUG_MODE:
        print(f"\n=== ROUTER AGENT: Analyzing query '{user_input}' ===")
    
    try:
        # OPTIMIZATION: Check cache with TTL first
        cached_route = get_cached_route(user_input)
        if cached_route:
            return {"data_source": cached_route}
        
        # OPTIMIZATION: Check if query matches a known SQL template
        # If it does, we can skip the LLM router significantly reducing latency and ensuring accuracy
        template_sql = get_sql_from_template(user_input)
        if template_sql:
            if DEBUG_MODE:
                 print(f"Router Optimization: SQL Template matched. Forcing SQL_DB route.")
            # Cache for future
            cache_route(user_input, "sql")
            return {"data_source": "sql"}
        
        # Cache miss: run LLM classification
        chain = get_router_chain()
        result = chain.invoke({"input": user_input})

        decision = result.strip().upper()
        
        # Clean up decision
        if "SQL_DB" in decision:
            decision = "SQL_DB"
        elif "KNOWLEDGE_BASE" in decision:
            decision = "KNOWLEDGE_BASE"
        elif "GENERAL" in decision:
            decision = "GENERAL"
            
        if DEBUG_MODE:
            print(f"Router Decision: {decision}")
        
        # Map to data_source
        if decision == "SQL_DB":
            data_source = "sql"
        else:
            # Default to retriever for knowledge base and general
            data_source = "retriever"
        
        # OPTIMIZATION: Cache the decision with TTL
        cache_route(user_input, data_source)
            
        return {
            "data_source": data_source
        }
        
    except Exception as e:
        print(f"Router Error: {e}")
        # Fallback to retriever
        return {
            "data_source": "retriever"
        }

