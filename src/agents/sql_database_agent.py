import os
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.utils.db_connection import get_supabase_db
from src.utils.llm_singleton import get_llm
from src.utils.yaml_loader import load_prompts
from src.schemas.response_schema import ResponseSchema
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from src.utils.schema_context import DB_SCHEMA_CONTEXT

def get_sql_prompts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "..", "utils", "prompts.yml")
    return load_prompts(prompts_path)

def query_database_chain(user_query: str):
    """
    Execute SQL Chain: Generate SQL -> Execute -> Synthesize
    """
    t0 = time.time()
    try:
        # 1. Setup
        llm = get_llm(model="gemini-2.5-flash", temperature=0)
        db = get_supabase_db()  # Singleton (fast if already warm)
        prompts = get_sql_prompts()
        
        # 2. Generate SQL
        t1 = time.time()
        gen_prompt_str = prompts.get("sql_generation_prompt", "")
        gen_prompt = ChatPromptTemplate.from_template(
            gen_prompt_str + "\n\nSchema:\n{schema}\n\nQuestion: {question}"
        )
            
        generate_chain = (
            RunnablePassthrough.assign(schema=lambda _: DB_SCHEMA_CONTEXT)
            | gen_prompt
            | llm
            | StrOutputParser()
        )
        
        sql_query = generate_chain.invoke({"question": user_query})
        sql_query = sql_query.strip().replace("```sql", "").replace("```", "")
        t2 = time.time()
        print(f"SQL Generated ({t2-t1:.2f}s): {sql_query}")
        
        if "I don't know" in sql_query or not sql_query:
            return ""

        # 3. Execute SQL
        execute_tool = QuerySQLDataBaseTool(db=db)
        # Handle cases where LLM might return explanatory text
        if "SELECT" not in sql_query.upper():
             print("Invalid SQL generated")
             return ""
             
        db_result = execute_tool.invoke(sql_query)
        t3 = time.time()
        print(f"SQL Executed ({t3-t2:.2f}s): {str(db_result)[:100]}...")
        
        if not db_result:
            return ""

        # 4. Synthesize Answer
        syn_prompt_str = prompts.get("sql_synthesis_prompt", "")
        syn_prompt = ChatPromptTemplate.from_template(syn_prompt_str)
        
        syn_chain = syn_prompt | llm | StrOutputParser()
        response = syn_chain.invoke({"question": user_query, "result": db_result})
        t4 = time.time()
        
        print(f"Synthesis ({t4-t3:.2f}s). Total Chain: {t4-t0:.2f}s")
        return response.strip()

    except Exception as e:
        print(f"SQL Chain Error: {e}")
        return ""

def sql_agent_node(state: ResponseSchema) -> ResponseSchema:
    """
    Workflow node for SQL Chain.
    """
    user_query = state["user_query"]
    instruction = state.get("instruction", "")
    weather_info = state.get("weather_info", "")
    
    # Result from Intent Router
    intent = state.get("data_source", "") # "sql", "retriever"
    
    # If routed to SQL, execute chain
    if intent == "sql":
        response = query_database_chain(user_query)
        
        # Check if meaningful
        if response and "I don't know" not in response and "no information" not in response.lower():
             return {
                "user_query": user_query,
                "query_response": response,
                "evaluation_state": "",
                "retry_count": state.get("retry_count", 0),
                "instruction": instruction,
                "data_source": "sql",
                "weather_info": weather_info,
                "needs_escalation": False
            }
    
    # Fallback to retriever (if sql failed or intent wasn't sql - though workflow should handle that)
    return {
        "user_query": user_query,
        "query_response": "",
        "evaluation_state": "",
        "retry_count": state.get("retry_count", 0),
        "instruction": instruction,
        "data_source": "", # Empty source triggers next step fallback
        "weather_info": weather_info,
        "needs_escalation": False
    }

if __name__ == "__main__":
    # Test script
    print("Testing SQL Chain...")
    q = "tell me the tourist highlights in gondia?"
    ans = query_database_chain(q)
    print(f"Final Answer: {ans}")
