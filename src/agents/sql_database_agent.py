import os
import time
import signal
import traceback
from contextlib import contextmanager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.utils.db_connection import get_supabase_db
from src.utils.llm_singleton import get_llm
from src.utils.yaml_loader import load_prompts
from src.schemas.response_schema import ResponseSchema
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from src.utils.schema_context import DB_SCHEMA_CONTEXT
# OPTIMIZATION: Import SQL template cache and schema pruner
from src.agents.sql_template_cache import get_sql_from_template
from src.utils.schema_pruner import get_pruned_schema
# OPTIMIZATION: SQL Result Caching
from src.agents.sql_result_cache import get_cached_sql_result, cache_sql_result

# Phase 7: Schema Pruning Configuration
ENABLE_SCHEMA_PRUNING = os.getenv("ENABLE_SCHEMA_PRUNING", "true").lower() == "true"

@contextmanager
def timeout(seconds):
    """Context manager for timing out operations."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds}s")
    
    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        # Restore the old signal handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def get_sql_prompts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "..", "utils", "prompts.yml")
    return load_prompts(prompts_path)

def query_database_chain(user_input: str):
    """
    Execute SQL Chain: Generate SQL -> Execute -> Synthesize
    With 5-second total timeout to prevent hanging.
    """
    t0 = time.time()
    try:
        # Wrap entire chain in 30-second timeout (remote DB can be slow)
        with timeout(30):
            # 1. Setup
            llm = get_llm(model="gemini-2.5-flash", temperature=0)
            db = get_supabase_db()  # Singleton (fast if already warm)
            prompts = get_sql_prompts()
            
            # 2. Generate SQL
            t1 = time.time()
            pruned_schema = ""
            
            # OPTIMIZATION: Try template cache first
            sql_query = get_sql_from_template(user_input)
            
            if not sql_query:
                # Template cache miss - use LLM generation
                # OPTIMIZATION: Use pruned schema instead of full DB_SCHEMA_CONTEXT
                pruned_schema = get_pruned_schema(user_input, enable_pruning=ENABLE_SCHEMA_PRUNING)
                
                gen_prompt_str = prompts.get("sql_generation_prompt", "")
                gen_prompt = ChatPromptTemplate.from_template(
                    gen_prompt_str + "\n\nSchema:\n{schema}\n\nQuestion: {question}"
                )
                    
                generate_chain = (
                    RunnablePassthrough.assign(schema=lambda _: pruned_schema)  # ← Using pruned schema
                    | gen_prompt
                    | llm
                    | StrOutputParser()
                )
                
                sql_query = generate_chain.invoke({"question": user_input})
                sql_query = sql_query.strip().replace("```sql", "").replace("```", "")
            
            t2 = time.time()
            print(f"[SQL_AGENT] SQL Generated ({t2-t1:.2f}s): {sql_query}")
            print(f"[SQL_AGENT] Pruned Schema Used: {pruned_schema[:200]}..." if ENABLE_SCHEMA_PRUNING else "[SQL_AGENT] Full schema used")
            
            if "I don't know" in sql_query or not sql_query:
                return ""
            
            # OPTIMIZATION: Check SQL result cache before execution
            cached_result = get_cached_sql_result(user_input, sql_query)
            if cached_result:
                t_cache = time.time()
                print(f"[SQL_AGENT] Cache hit! Total time: {t_cache-t0:.2f}s")
                return cached_result

            # 3. Execute SQL with 12-second timeout (Supabase cold starts can take time)
            execute_tool = QuerySQLDataBaseTool(db=db)
            # Handle cases where LLM might return explanatory text
            if "SELECT" not in sql_query.upper():
                 print("Invalid SQL generated")
                 return ""
            
            # Execute with timeout
            with timeout(12):
                db_result = execute_tool.invoke(sql_query)
            
            t3 = time.time()
            print(f"[SQL_AGENT] SQL Executed ({t3-t2:.2f}s)")
            print(f"[SQL_AGENT] Result Preview: {str(db_result)[:200]}...")
            print(f"[SQL_AGENT] Result Length: {len(str(db_result))} chars")
            
            if not db_result:
                return ""

            # 4. Synthesize Answer
            syn_prompt_str = prompts.get("sql_synthesis_prompt", "")
            syn_prompt = ChatPromptTemplate.from_template(syn_prompt_str)
            
            syn_chain = syn_prompt | llm | StrOutputParser()
            response = syn_chain.invoke({"question": user_input, "result": db_result})

            t4 = time.time()
            
            print(f"[SQL_AGENT] Synthesis ({t4-t3:.2f}s). Total Chain: {t4-t0:.2f}s")
            print(f"[SQL_AGENT] Final Response Preview: {response[:100]}...")
            
            # OPTIMIZATION: Cache the result for future queries
            cache_sql_result(user_input, sql_query, response.strip())
            
            return response.strip()

    except TimeoutError as e:
        print(f"[SQL_AGENT] ❌ TIMEOUT after 10s: {e}")
        print(f"[SQL_AGENT] Falling back to retriever agent")
        return ""  # Return empty to trigger fallback to retriever
    except Exception as e:
        print(f"[SQL_AGENT] ❌ ERROR: {type(e).__name__}: {e}")
        print(f"[SQL_AGENT] Traceback: {traceback.format_exc()}")
        return ""

def sql_agent_node(state: ResponseSchema) -> ResponseSchema:
    """
    Workflow node for SQL Chain.
    """
    user_input = state["validated_user_input"]

    instruction = state.get("instruction", "")
    weather_info = state.get("weather_info", "")
    
    # Result from Intent Router
    intent = state.get("data_source", "") # "sql", "retriever"
    
    # If routed to SQL, execute chain
    if intent == "sql":
        response = query_database_chain(user_input)

        if response:
             return {
                "query_response": response,
                "data_source": "sql",
                "needs_escalation": False
            }
    
    # Fallback to retriever only if SQL execution failed or returned no data
    return {
        "query_response": "",
        "data_source": "", 
        "needs_escalation": False
    }


if __name__ == "__main__":
    # Test script
    print("Testing SQL Chain...")
    q = "tell me the tourist highlights in gondia?"
    ans = query_database_chain(q)
    print(f"Final Answer: {ans}")
