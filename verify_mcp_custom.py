
import asyncio
import os
import uuid
import httpx
from dotenv import load_dotenv

async def verify_custom_sse():
    load_dotenv()
    url = "https://mcp.supabase.com/mcp?project_ref=pqtsnastghvwdinzxxfz&read_only=true"
    token = os.getenv("SUPABASE_DB_ACCESS_TOKEN") # The PAT
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Mcp-Session-Id": str(uuid.uuid4()),
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    
    print(f"Connecting to: {url}")
    try:
        async with httpx.AsyncClient() as client:
            session_id = str(uuid.uuid4())
            headers["Mcp-Session-Id"] = session_id
            
            # 1. Initialize
            print(f"--- 1. Sending Initialize (Session: {session_id}) ---")
            init_payload = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "verify", "version": "1.0"}
                },
                "id": 1
            }
            resp1 = await client.post(url, headers=headers, json=init_payload, timeout=10.0)
            print(f"Init Status: {resp1.status_code}")
            print(f"Init Body: {resp1.text}")
            
            if resp1.status_code != 200:
                print("❌ Init Failed")
                return False

            # 2. List Tools
            print(f"\n--- 2. Sending Tools/List ---")
            tools_payload = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }
            resp2 = await client.post(url, headers=headers, json=tools_payload, timeout=10.0)
            print(f"Tools Status: {resp2.status_code}")
            print(f"Tools Body: {resp2.text[:500]}...") # truncate
            
            if resp2.status_code == 200 and "tools" in resp2.text:
                print("✅ HTTP JSON-RPC Protocol Confirmed!")
                return True
            else:
                print("❌ Tools/List Failed")
                return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(verify_custom_sse())
