from langgraph.graph import StateGraph, START, END
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from settings import GOOGLE_API_KEY 
from src.agents.evaluator_agent import evaluator_agent
from src.agents.retriver_agent import retriver_agent
from datetime import datetime, timedelta
from src.agents.response_enricher import response_enricher_node
from src.schemas.response_schema import ResponseSchema
from src.agents.sql_database_agent import sql_agent_node
from src.agents.weather_enricher import weather_enricher_node
from src.agents.router_agent import router_agent_node
from src.agents.supabase_mcp_agent import supabase_mcp_agent_node   # <--- Import MCP Agent
from src.utils.config import USE_MCP_AGENT                          # <--- Import Flag

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)


def evaluation_edge(state: ResponseSchema):
    """Determine next node based on evaluation and escalation status."""
    # If escalation is needed, go to END
    if state.get("needs_escalation", False):
        return END
    
    # If evaluation passed, go to END
    if state.get("evaluation_state") == "True":
        return END
    
    # If evaluation failed but retry limit not exceeded, retry with retriver_agent
    if state.get("retry_count", 0) < 3:
        return "retriver_agent"
    
    return END

def intent_routing_edge(state: ResponseSchema):
    """Route based on Intent Router decision."""
    source = state.get("data_source", "retriever")
    if source == "sql":
        if USE_MCP_AGENT:
             return "supabase_mcp_agent"  # <--- Route to MCP Agent
        return "sql_agent"
    return "retriver_agent"

def sql_routing_edge(state: ResponseSchema):
    """Route based on whether SQL agent found an answer."""
    # If SQL/MCP agent returned a valid response, go to enricher
    if state.get("query_response") and state.get("data_source") == "sql":
        return "response_enricher"
    # Fallback to retriever
    return "retriver_agent"


def retriever_routing_edge(state: ResponseSchema):
    """Route based on whether retriever agent found an answer."""
    query_response = state.get("query_response", "")
    
    # Ensure query_response is a string (handle multimodal list responses)
    if isinstance(query_response, list):
        text_parts = []
        for part in query_response:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        query_response = "".join(text_parts)
    
    # Patterns that indicate no answer was found
    no_answer_patterns = [
        "i don't know",
        "i do not know",
        "i cannot answer",
        "i'm unable to help",
        "i am unable to help",
        "no information",
        "sorry, i am not able to help with this question. Please try asking something different.",
        "please try asking something different"
    ]
    
    # Check if retriever found a meaningful answer
    response_lower = str(query_response).lower()
    has_no_answer = any(pattern in response_lower for pattern in no_answer_patterns)
    has_answer = bool(query_response) and not has_no_answer
    
    if has_answer:
        # Retriever found answer, go to response enricher
        return "response_enricher"
    # No answer from retriever, go to evaluator (which will set escalation)
    return "evaluator_agent"


from src.agents.pre_processor import pre_processor_node

async def atomic_workflow(state: ResponseSchema) -> ResponseSchema:
    """
    Executes the entire chatbot pipeline as a single async atomic step.
    This bypasses LangGraph state merging conflicts and reduces overhead.
    """
    # 1. Pre-processing (Weather + Router) - Now Async
    pre_res = await pre_processor_node(state)
    state.update(pre_res)
    
    # 2. Intent Routing & Data Retrieval
    source = intent_routing_edge(state)
    
    if source == "supabase_mcp_agent":
        # Execute Supabase MCP Agent (Async)
        sql_res = await supabase_mcp_agent_node(state)
        state.update(sql_res)
        
        # Check if successful
        next_step = sql_routing_edge(state)
        if next_step == "retriver_agent":
            # Fallback to Retriever (Async)
            ret_res = await retriver_agent(state)
            state.update(ret_res)
            
    elif source == "sql_agent":
        # Legacy SQL Agent (Sync version) - run in thread for safety
        sql_res = await asyncio.to_thread(sql_agent_node, state)
        state.update(sql_res)
        
        if not state.get("query_response") and not state.get("sql_empty_result"):
            ret_res = await retriver_agent(state)
            state.update(ret_res)
    else:
        # Direct to Retriever (Async)
        ret_res = await retriver_agent(state)
        state.update(ret_res)
    
    # 3. Response Enrichment (Sync-ish) - run in thread
    enr_res = await asyncio.to_thread(response_enricher_node, state)
    state.update(enr_res)
    
    # 4. Evaluation (Sync-ish) - run in thread
    eval_res = await asyncio.to_thread(evaluator_agent, state)
    state.update(eval_res)
    
    return {
        "query_response": state.get("query_response", ""),
        "evaluation_state": state.get("evaluation_state", ""),
        "retry_count": state.get("retry_count", 0),
        "data_source": state.get("data_source", ""),
        "weather_info": state.get("weather_info", ""),
        "needs_escalation": state.get("needs_escalation", False)
    }



# Build the atomic graph
graph = StateGraph(ResponseSchema)
graph.add_node('atomic_chat', atomic_workflow)
graph.add_edge(START, 'atomic_chat')
graph.add_edge('atomic_chat', END)

workflow = graph.compile()


