from datetime import datetime
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.llm_singleton import get_llm
from src.utils.yaml_loader import load_prompts
from src.schemas.response_schema import ResponseSchema
from settings import ORGANIZATION_NAME

def get_router_chain():
    """Create the router chain."""
    llm = get_llm(model="gemini-2.5-flash", temperature=0)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "..", "utils", "prompts.yml")
    prompts = load_prompts(prompts_path)
    
    prompt_text = prompts.get("router_agent_prompt", "")
    
    prompt = ChatPromptTemplate.from_template(prompt_text + "\n\nQUERY: {input}")
    chain = prompt | llm | StrOutputParser()
    return chain

def router_agent_node(state: ResponseSchema) -> ResponseSchema:
    """
    Classify the user query to determine the best data source.
    """
    user_query = state["user_query"]
    print(f"\n=== ROUTER AGENT: Analyzing query '{user_query}' ===")
    
    try:
        chain = get_router_chain()
        result = chain.invoke({"input": user_query})
        decision = result.strip().upper()
        
        # Clean up decision
        if "SQL_DB" in decision:
            decision = "SQL_DB"
        elif "KNOWLEDGE_BASE" in decision:
            decision = "KNOWLEDGE_BASE"
        elif "GENERAL" in decision:
            decision = "GENERAL"
            
        print(f"Router Decision: {decision}")
        
        # Map to data_source
        if decision == "SQL_DB":
            data_source = "sql"
        else:
            # Default to retriever for knowledge base and general (retriever handles general well enough or fails gracefully)
            data_source = "retriever"
            
        return {
            "user_query": user_query,
            "query_response": "",
            "evaluation_state": "",
            "retry_count": state.get("retry_count", 0),
            "instruction": "",
            "data_source": data_source,
            "weather_info": state.get("weather_info", ""),
            "needs_escalation": False
        }
        
    except Exception as e:
        print(f"Router Error: {e}")
        # Fallback to retriever
        return {
            "user_query": user_query,
            "query_response": "",
            "evaluation_state": "",
            "retry_count": state.get("retry_count", 0),
            "instruction": "",
            "data_source": "retriever",
            "weather_info": state.get("weather_info", ""),
            "needs_escalation": False
        }
