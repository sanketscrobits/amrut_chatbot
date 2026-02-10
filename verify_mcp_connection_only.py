
import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from src.utils.config import SUPABASE_MCP_URL

async def verify_connection():
    load_dotenv()
    headers = {
        "Authorization": f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}"
    }
    print(f"Connecting to: {SUPABASE_MCP_URL}")
    print("Using Authorization: Bearer <SERVICE_ROLE_KEY>")
    
    try:
        async with sse_client(SUPABASE_MCP_URL, headers=headers) as (read, write):
            print("✅ SSE Connection Established.")
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ Session Initialized.")
                
                # List tools
                tools = await session.list_tools()
                print(f"Available Tools: {[t.name for t in tools.tools]}")
                
                # Try simple schema fetch if list_tables exists
                if any(t.name == "list_tables" for t in tools.tools):
                    tables = await session.call_tool("list_tables", arguments={})
                    print(f"Tables: {tables.content[0].text}")
                    return True
                else:
                    print("⚠️ 'list_tables' tool not found.")
                    return True

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(verify_connection())
