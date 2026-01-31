from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from settings import GOOGLE_API_KEY 
from src.agents.evaluator_agent import evaluator_agent
from src.agents.retriver_agent import retriver_agent
from src.schemas.response_schema import ResponseSchema
from src.agents.sql_database_agent import sql_agent_node
from src.agents.weather_enricher import weather_enricher_node

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key = GOOGLE_API_KEY)

def evaluation_edge(state: ResponseSchema):
    return "retriver_agent" if state["evaluation_state"] == "False" else END

def sql_routing_edge(state: ResponseSchema):
    """Route based on whether SQL agent found an answer."""
    if state.get("query_response") and state.get("data_source") == "sql":
        return "evaluator_agent"
    return "retriver_agent" 

graph = StateGraph(ResponseSchema)

graph.add_node('weather_enricher', weather_enricher_node)
graph.add_node('sql_agent', sql_agent_node)
graph.add_node('retriver_agent', retriver_agent)
graph.add_node('evaluator_agent', evaluator_agent)

# Start with weather enrichment
graph.add_edge(START, 'weather_enricher')

# Then go to SQL agent (which will now have weather context if applicable)
graph.add_edge('weather_enricher', 'sql_agent')

graph.add_conditional_edges(
    "sql_agent",
    sql_routing_edge,
    {
        "evaluator_agent": "evaluator_agent",
        "retriver_agent": "retriver_agent"
    }
)
graph.add_edge('retriver_agent', 'evaluator_agent')
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
        "instruction": ""
    }

    final_state = workflow.invoke(initial_state, config={"verbose": True})

    print(final_state)
