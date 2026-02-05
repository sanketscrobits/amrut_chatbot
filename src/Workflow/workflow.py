from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from settings import GOOGLE_API_KEY 
from src.agents.evaluator_agent import evaluator_agent
from src.agents.retriver_agent import retriver_agent
from src.agents.response_enricher import response_enricher_node
from src.schemas.response_schema import ResponseSchema
from src.agents.sql_database_agent import sql_agent_node
from src.agents.weather_enricher import weather_enricher_node
from src.agents.router_agent import router_agent_node

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
        return "sql_agent"
    return "retriver_agent"

def sql_routing_edge(state: ResponseSchema):
    """Route based on whether SQL agent found an answer."""
    # If SQL agent returned a valid response, go to enricher
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


# Build the graph
graph = StateGraph(ResponseSchema)

# Add nodes
graph.add_node('weather_enricher', weather_enricher_node)
graph.add_node('router_agent', router_agent_node)
graph.add_node('sql_agent', sql_agent_node)
graph.add_node('retriver_agent', retriver_agent)
graph.add_node('response_enricher', response_enricher_node)
graph.add_node('evaluator_agent', evaluator_agent)

# Define edges
# Start -> Weather -> Router
graph.add_edge(START, 'weather_enricher')
graph.add_edge('weather_enricher', 'router_agent')

# Router -> SQL or Retriever
graph.add_conditional_edges(
    "router_agent",
    intent_routing_edge,
    {
        "sql_agent": "sql_agent",
        "retriver_agent": "retriver_agent"
    }
)

# SQL Agent -> Response Enricher (Success) or Retriever (Fallback)
graph.add_conditional_edges(
    "sql_agent",
    sql_routing_edge,
    {
        "response_enricher": "response_enricher",
        "retriver_agent": "retriver_agent"
    }
)

# Retriever routing: answer found → response_enricher, no answer → evaluator (for escalation)
graph.add_conditional_edges(
    "retriver_agent",
    retriever_routing_edge,
    {
        "response_enricher": "response_enricher",
        "evaluator_agent": "evaluator_agent"
    }
)

# Response enricher always goes to evaluator
graph.add_edge('response_enricher', 'evaluator_agent')

# Evaluator routing: profanity retry → retriver_agent, pass/escalation → END
graph.add_conditional_edges(
    "evaluator_agent",
    evaluation_edge,
    {
        "retriver_agent": "retriver_agent",
        END: END
    }
)

workflow = graph.compile()

if __name__ == "__main__":
    initial_state = {
        "user_query": "tell me the tourist highlights in gondia?",
        "query_response": "",
        "evaluation_state": "",
        "retry_count": 0,
        "instruction": "",
        "data_source": "",
        "weather_info": "",
        "needs_escalation": False
    }

    final_state = workflow.invoke(initial_state, config={"verbose": True})

    print(final_state)
