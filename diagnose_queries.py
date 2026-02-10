
import asyncio
import sys
from src.agents.supabase_mcp_agent import run_mcp_chain

# Queries to diagnose
DIAGNOSTIC_QUERIES = [
    "List hospitals in Pune"
]

async def diagnose_queries():
    print("--- Deep Diagnosis of Failing Query: 'List hospitals in Pune' ---", flush=True)
    
    for query in DIAGNOSTIC_QUERIES:
        print(f"\n\n{'='*60}", flush=True)
        print(f"QUERY: {query}", flush=True)
        print(f"{'='*60}", flush=True)
        
        try:
            response = await run_mcp_chain(query)
            print(f"\nFINAL RESPONSE: {response}", flush=True)
            
        except Exception as e:
            print(f"ERROR: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(diagnose_queries())
