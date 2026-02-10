import os
import time
import asyncio
import traceback
import uuid
import httpx
import json
from contextlib import asynccontextmanager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from mcp import ClientSession, ClientSession, ClientSession
from mcp.types import JSONRPCMessage, JSONRPCRequest, JSONRPCResponse, JSONRPCNotification
import mcp.types as types
from src.utils.llm_singleton import get_llm
from src.utils.yaml_loader import load_prompts
from src.schemas.response_schema import ResponseSchema
from src.utils.config import SUPABASE_MCP_URL

from mcp.shared.session import SessionMessage

# --- Custom HTTP Transport for Supabase MCP ---
# Supabase MCP uses stateless/stateful HTTP JSON-RPC over POST, not SSE.
# ClientSession expects a ReadStream (async iterator) and WriteStream (write_message method).

class SupabaseHttpTransport:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.session_id = str(uuid.uuid4())
        self._client = None
        self._read_queue = asyncio.Queue()
        
    async def start(self):
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            
    # ReadStream Interface
    def __aiter__(self):
        return self
        
    async def __anext__(self):
        item = await self._read_queue.get()
        if isinstance(item, Exception):
            raise item
        return item

    # WriteStream Interface
    async def write_message(self, message: JSONRPCMessage):
        if not self._client:
            raise RuntimeError("Transport not started")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "apikey": self.api_key,
            "Mcp-Session-Id": self.session_id,
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        }
        
        # Unwrap SessionMessage if needed
        # mcp.shared.session sends SessionMessage(message=JSONRPCMessage(...), metadata=...)
        if hasattr(message, "message"):
            rpc_message = message.message
        else:
            rpc_message = message
        
        # Serialize message
        # Serialize message
        payload = rpc_message.model_dump(
            mode="json", 
            by_alias=True, 
            exclude_none=True
        )
        # print(f"[Transport] Sending: {json.dumps(payload)}")
        
        try:
            resp = await self._client.post(self.url, headers=headers, json=payload)
            
            if resp.status_code >= 300:
                print(f"[Transport] ❌ Error {resp.status_code}: {resp.text}")
                raise RuntimeError(f"Supabase MCP Error {resp.status_code}: {resp.text}")
            
            if resp.status_code == 202:
                # 202 Accepted - unexpected for JSON-RPC usually. Check body.
                print(f"[Transport] ⚠️ Got 202. Body: {resp.text[:1000]}", flush=True)
            
            # DEBUG: Always print body
            print(f"[Transport] Response Body: {resp.text[:1000]}", flush=True)
                
            # Parse response
            if not resp.text.strip():
                 # Empty body
                 return
                 
            data = resp.json()
            
            parsed_msg = None
            
            # Check for standard fields
            if "method" in data:
                 if "id" in data:
                     parsed_msg = types.JSONRPCRequest.model_validate(data)
                 else:
                     parsed_msg = types.JSONRPCNotification.model_validate(data)
            elif "result" in data or "error" in data:
                 parsed_msg = types.JSONRPCResponse.model_validate(data)
            else:
                 print(f"[Transport] Unknown message format: {data}")
                 pass
                 
            if parsed_msg:
                # Wrap in JSONRPCMessage RootModel as required by SessionMessage
                # SessionMessage.message field expects JSONRPCMessage (RootModel) which has .root
                root_msg = types.JSONRPCMessage(root=parsed_msg)
                
                # Wrap in SessionMessage as expected by ClientSession._receive_loop
                session_msg = SessionMessage(message=root_msg, metadata={})
                await self._read_queue.put(session_msg)
                
        except Exception as e:
            print(f"[Transport] Request Failed: {e}")
            await self._read_queue.put(e)

    # Alias for mcp.shared.session.Session compatibility
    async def send(self, message: JSONRPCMessage):
        await self.write_message(message)

    # Context Manager compatibility for ClientSession
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@asynccontextmanager
async def supabase_mcp_client(url: str = SUPABASE_MCP_URL):
    # Load keys
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("SUPABASE_DB_ACCESS_TOKEN")
    
    if not token:
        print("[MCP_AGENT] ⚠️ Missing SUPABASE_DB_ACCESS_TOKEN via dotenv. Checking os.environ...")
        token = os.environ.get("SUPABASE_DB_ACCESS_TOKEN")
        
    if not token:
        raise ValueError("Missing SUPABASE_DB_ACCESS_TOKEN. Cannot connect to Supabase MCP.")

    transport = SupabaseHttpTransport(url, token)
    await transport.start()
    
    try:
        # ClientSession(read, write)
        async with ClientSession(transport, transport) as session:
            yield session
    finally:
        await transport.close()


# --- Schema Management ---
_MCP_SCHEMA_CACHE = {}

async def get_mcp_schema(session: ClientSession) -> str:
    global _MCP_SCHEMA_CACHE
    if "full_schema" in _MCP_SCHEMA_CACHE:
        return _MCP_SCHEMA_CACHE["full_schema"]
        
    try:
        tables_result = await session.call_tool("list_tables", arguments={})
        
        # The Supabase MCP 'list_tables' tool returns a JSON string containing the full schema definition
        # We should parse this directly instead of running a separate SQL introspection query
        # which might fail or be redundant.
        
        tables_json_str = tables_result.content[0].text
        tables_data = json.loads(tables_json_str)
        
        formatted_schema = "Schema Definitions:\n\n"
        
        # Iterate over the parsed JSON to build the schema context string
        for table in tables_data:
            table_name = table.get("name")
            schema_name = table.get("schema", "public")
            
            # Skip internal or irrelevant tables if needed, but for now include all public ones
            if schema_name != "public":
                continue
                
            formatted_schema += f"Table: {table_name}\n"
            formatted_schema += f"Description: {table.get('description', 'No description')}\n"
            formatted_schema += "Columns:\n"
            
            for col in table.get("columns", []):
                col_name = col.get("name")
                col_type = col.get("data_type")
                is_pk = "primary_keys" in table and col_name in table["primary_keys"]
                pk_str = " (PK)" if is_pk else ""
                formatted_schema += f"  - {col_name} ({col_type}){pk_str}\n"
            
            formatted_schema += "\n"

        _MCP_SCHEMA_CACHE["full_schema"] = formatted_schema
        print("[MCP_AGENT] ✅ Schema fetched and cached (via list_tables parsing).")
        return formatted_schema
    except Exception as e:
        print(f"[MCP_AGENT] ⚠️ Failed to fetch schema: {e}")
        return "Schema unavailable due to error."

def get_sql_prompts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "..", "utils", "prompts.yml")
    return load_prompts(prompts_path)

async def run_mcp_chain(user_input: str):
    t0 = time.time()
    try:
        async with supabase_mcp_client() as session:
            await session.initialize()
            
            # 1. Setup
            llm = get_llm(model="gemini-2.5-flash", temperature=0)
            prompts = get_sql_prompts()
            
            # 2. Schema
            schema_context = await get_mcp_schema(session)
            
            # 3. Generate SQL
            t1 = time.time()
            gen_prompt_str = prompts.get("sql_generation_prompt", "")
            gen_prompt = ChatPromptTemplate.from_template(
                gen_prompt_str + "\n\nSchema Context from MCP:\n{schema}\n\nQuestion: {question}"
            )
            generate_chain = gen_prompt | llm | StrOutputParser()
            
            print(f"[MCP_AGENT] Invoking LLM for SQL generation...", flush=True)
            sql_query = await generate_chain.ainvoke({"schema": schema_context, "question": user_input})
            print(f"[MCP_AGENT] LLM Returned...", flush=True)
            
            sql_query = sql_query.strip().replace("```sql", "").replace("```", "")
            
            t2 = time.time()
            print(f"[MCP_AGENT] SQL Generated ({t2-t1:.2f}s): {sql_query}")
            
            if "I don't know" in sql_query or not sql_query:
                return ""
            if "SELECT" not in sql_query.upper():
                 return ""
            
            print("[MCP_AGENT] 🚀 Executing via MCP...")
            result = await session.call_tool("execute_sql", arguments={"query": sql_query})
            db_result = result.content[0].text
            print(f"[MCP_AGENT] DB Result: {db_result[:500]}...", flush=True)
            
            t3 = time.time()
            print(f"[MCP_AGENT] SQL Executed ({t3-t2:.2f}s)", flush=True)
            
            # 5. Synthesize
            syn_prompt_str = prompts.get("sql_synthesis_prompt", "")
            syn_prompt = ChatPromptTemplate.from_template(syn_prompt_str)
            syn_chain = syn_prompt | llm | StrOutputParser()
            response = await syn_chain.ainvoke({"question": user_input, "result": db_result})
            
            return response.strip()

    except Exception as e:
        print(f"[MCP_AGENT] ❌ ERROR: {e}")
        print(traceback.format_exc())
        return ""

def query_mcp_chain_sync(user_input: str) -> str:
    try:
        return asyncio.run(run_mcp_chain(user_input))
    except Exception as e:
        print(f"[MCP_AGENT] Sync Wrapper Error: {e}")
        return ""

async def supabase_mcp_agent_node(state: ResponseSchema) -> ResponseSchema:
    """
    Async version of MCP Agent node for the master workflow.
    """
    user_input = state["validated_user_input"]
    print(f"[MCP_AGENT] 🤖 Processing: {user_input}", flush=True)
    
    try:
        response = await run_mcp_chain(user_input)
        
        if response and "I don't know" not in response and "unable to help" not in response:
            return {
                "query_response": response,
                "data_source": "sql",
                "evaluation_state": "True"
            }
    except Exception as e:
        print(f"[MCP_AGENT] Async Node Error: {e}", flush=True)
        traceback.print_exc()
        
    return {
        "query_response": "",
        "data_source": "sql",
        "evaluation_state": "False"
    }

def supabase_mcp_agent_node_sync(state: ResponseSchema) -> ResponseSchema:
    """
    Legacy sync version for backward compatibility.
    """
    user_input = state["validated_user_input"]
    response = query_mcp_chain_sync(user_input)
    
    if response:
        return {
            "query_response": response,
            "data_source": "sql",
            "evaluation_state": "True"
        }
    
    return {
        "query_response": "",
        "data_source": "sql", 
        "evaluation_state": "False"
    }
