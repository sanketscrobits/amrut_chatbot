from src.schemas.response_schema import ResponseSchema
from settings import GOOGLE_API_KEY
from src.agents.query_agent import create_query_agent

# Build the query agent once; uses the get_context tool under the hood
query_agent = create_query_agent(api_key=GOOGLE_API_KEY)


def extract_text_from_content(content) -> str:
    """Extract text from LLM content which may be string or list (multimodal)."""
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        return "".join(text_parts).strip()
    return str(content).strip() if content else ""


def retriver_agent(state: ResponseSchema) -> ResponseSchema:
    user_query = state["user_query"]
    instruction = state.get("instruction", "")
    weather_info = state.get("weather_info", "")
    
    print(f"\n=== RETRIVER_AGENT CALLED ===")
    print(f"User query: {user_query}")
    print(f"Instruction: {instruction}")
    
    prompt_text = f"{user_query}\n\n{instruction}" if instruction else user_query
    print(f"Invoking query_agent with: {prompt_text[:100]}...")
    
    result = query_agent.invoke({"messages": [{"role": "user", "content": prompt_text}]})
    
    print(f"Agent result keys: {result.keys()}")
    print(f"Number of messages: {len(result.get('messages', []))}")
    
    # Print all messages to see tool calls
    for i, msg in enumerate(result.get("messages", [])):
        print(f"  Message {i}: role={getattr(msg, 'type', 'unknown')}, has_tool_calls={hasattr(msg, 'tool_calls')}")
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print(f"    Tool calls: {[tc.get('name', 'unknown') for tc in msg.tool_calls]}")
    
    # Extract text from potentially multimodal response
    raw_content = result["messages"][-1].content
    response_str = extract_text_from_content(raw_content)
    
    print(f"Final response: {response_str[:200]}...")
    print(f"=== RETRIVER_AGENT COMPLETE ===\n")

    return {
        "user_query": user_query,
        "query_response": response_str,
        "evaluation_state": "",
        "retry_count": state["retry_count"] + 1,
        "instruction": instruction,
        "data_source": "retriever",
        "weather_info": weather_info,
        "needs_escalation": False
    }
