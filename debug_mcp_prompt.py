
import asyncio
from src.agents.supabase_mcp_agent import run_mcp_chain

async def debug_prompt_construction():
    print("--- Debugging MCP Full Chain Execution ---")
    
    question = "How many districts are in Maharashtra?"
    
    print(f"\n[DEBUG] Running chain for: '{question}'")
    try:
        response = await run_mcp_chain(question)
        print(f"\n[DEBUG] Chain Result: {response}")
    except Exception as e:
        print(f"\n[DEBUG] Chain Failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_prompt_construction())
