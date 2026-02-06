from src.schemas.response_schema import ResponseSchema
from settings import GOOGLE_API_KEY
from src.tools.query_tool import get_context
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize LLM for answering based on context
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.1)


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
    
    # Step 1: Directly get context from vector database
    context = get_context.invoke(user_query)
    print(f"DEBUG Retriever: Got context from Pinecone: {context[:200]}..." if context else "DEBUG Retriever: No context")
    
    # Step 2: Check if meaningful context was found
    no_context_patterns = ["no relevant context", "error retrieving"]
    has_context = bool(context) and not any(p in context.lower() for p in no_context_patterns)
    
    if has_context:
        # Step 3: Use LLM to answer BASED ON the context
        prompt = f"""Answer the user's question based ONLY on the following context.
If the context doesn't contain enough information to fully answer, provide what you can from the context.

Context:
{context}

User Question: {user_query}

Answer:"""
        response = llm.invoke(prompt)
        response_str = extract_text_from_content(response.content)
    else:
        # No context found
        response_str = "Sorry, I am not able to help with this question. Please try asking something different."
    
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

