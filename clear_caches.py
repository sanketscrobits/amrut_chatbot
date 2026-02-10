
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.utils.semantic_cache import clear_semantic_cache
from src.utils.redis_client import clear_cache_pattern

def main():
    print("🧹 Clearing all chatbot caches...")
    
    # 1. Clear Semantic Cache
    if clear_semantic_cache():
        print("✅ Semantic cache cleared.")
    else:
        print("❌ Failed to clear semantic cache.")
        
    # 2. Clear Exact Match Cache
    try:
        clear_cache_pattern("response:*")
        print("✅ Exact match response cache cleared.")
    except Exception as e:
        print(f"⚠️ Error clearing response cache: {e}")
        
    # 3. Clear Router Cache
    try:
        clear_cache_pattern("router:*")
        print("✅ Router decision cache cleared.")
    except Exception as e:
        print(f"⚠️ Error clearing router cache: {e}")
        
    print("✨ All caches cleared.")

if __name__ == "__main__":
    main()
