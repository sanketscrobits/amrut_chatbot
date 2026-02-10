
import asyncio
from src.agents.supabase_mcp_agent import run_mcp_chain, query_mcp_chain_sync
from src.utils.db_connection import get_supabase_db

async def verify_mcp_schema_fetch():
    print("--- 🔍 Verifying MCP Schema Fetching ---")
    try:
        from src.agents.supabase_mcp_agent import get_mcp_schema, supabase_mcp_client
        import httpx
        
        print(f"Connecting using supabase_mcp_client (HTTP JSON-RPC)...")
        
        async with supabase_mcp_client() as session:
            await session.initialize()
            print("✅ Session Initialized.")
            
            # List tools to see what's available
            try:
                tools = await session.list_tools()
                print(f"Available Tools: {[t.name for t in tools.tools]}")
            except Exception as e:
                print(f"⚠️ Failed to list tools: {e}")
            
            schema = await get_mcp_schema(session)
            print(f"Schema Length: {len(schema)} chars")
            print(f"Schema Preview:\n{schema[:1000]}...")
            
            if len(schema) > 100:
                print("✅ Schema fetching SUCCESS (Content verified)")
                return True
            else:
                print("❌ Schema fetching FAILED (Empty or too short)")
                return False
                    
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        # print full traceback for debugging
        import traceback
        traceback.print_exc()
        print(f"❌ Schema fetching ERROR: {type(e).__name__}: {e}")
        return False

def verify_mcp_query():
    print("\n--- 🚀 Verifying MCP Query Execution ---")
    queries = [
        "How many districts are in Maharashtra?",
        "What is the population of Solapur?",
        "Tell me about Pune district"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        response = query_mcp_chain_sync(q)
        print(f"Response: {response}")
        
        if "I don't know" in response or not response:
            print("❌ Query FAILED")
        else:
            print("✅ Query SUCCESS")

if __name__ == "__main__":
    print("=== STARTING MCP AGENT VERIFICATION ===")
    
    # 1. Verify schema
    asyncio.run(verify_mcp_schema_fetch())
    
    # 2. Verify queries
    verify_mcp_query()
