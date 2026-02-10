
import asyncio
import json
from src.agents.supabase_mcp_agent import supabase_mcp_client

async def list_mcp_tools():
    print("--- Listing MCP Tools ---")
    async with supabase_mcp_client() as session:
        await session.initialize()
        
        print("\n[DEBUG] Calling tools/list...")
        tools_result = await session.list_tools()
        
        # Tools result is a ListToolsResult object, we need to inspect it
        for tool in tools_result.tools:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Input Schema: {json.dumps(tool.inputSchema, indent=2)}")

if __name__ == "__main__":
    asyncio.run(list_mcp_tools())
