
import asyncio
import os
import uuid
from dotenv import load_dotenv
from mcp.types import JSONRPCRequest
from src.agents.supabase_mcp_agent import SupabaseHttpTransport, SessionMessage

async def debug_transport():
    load_dotenv()
    token = os.getenv("SUPABASE_DB_ACCESS_TOKEN")
    url = "https://mcp.supabase.com/mcp?project_ref=pqtsnastghvwdinzxxfz&read_only=true"
    
    from mcp.types import JSONRPCMessage, JSONRPCResponse
    
    print("--- Testing JSONRPCMessage Wrapping ---")
    resp = JSONRPCResponse(jsonrpc="2.0", id=1, result={})
    print(f"Response object: {type(resp)}")
    
    try:
        # Try to wrap in RootModel
        wrapper = JSONRPCMessage(root=resp)
        print(f"Wrapper type: {type(wrapper)}")
        print(f"Wrapper root: {type(wrapper.root)}")
        
        session_msg = SessionMessage(message=wrapper, metadata={})
        print(f"SessionMessage.message type: {type(session_msg.message)}")
        if hasattr(session_msg.message, "root"):
            print("✅ SessionMessage.message has .root")
        else:
            print("❌ SessionMessage.message MISSING .root")
            
    except Exception as e:
        print(f"Wrapper failed: {e}")
        # Try direct assignment to see what happens
        session_msg = SessionMessage(message=resp, metadata={})
        print(f"Direct SessionMessage.message type: {type(session_msg.message)}")

    return

if __name__ == "__main__":
    asyncio.run(debug_transport())
