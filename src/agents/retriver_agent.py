from src.schemas.response_schema import ResponseSchema
from settings import GOOGLE_API_KEY
from src.agents.query_agent import create_query_agent

# Build the query agent once; uses the get_context tool under the hood
query_agent = create_query_agent(api_key=GOOGLE_API_KEY)

def retriver_agent(state: ResponseSchema) -> ResponseSchema:
    user_query = state["user_query"]
    instruction = state["instruction"]
    prompt_text = f"{user_query}\n\n{instruction}" if instruction else user_query
    result = query_agent.invoke({"messages": [{"role": "user", "content": prompt_text}]})
    response_str = result["messages"][-1].content

    return {
        "user_query": user_query,
        "query_response": response_str,
        "evaluation_state": "",
        "retry_count": state["retry_count"] + 1,
        "instruction": instruction
    }
