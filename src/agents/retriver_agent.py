from src.schemas.response_schema import ResponseSchema
from settings import GOOGLE_API_KEY, ORGANIZATION_NAME, DEBUG_MODE
from src.utils.llm_singleton import get_llm
from src.tools.query_tool import get_context
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def retriver_agent(state: ResponseSchema) -> ResponseSchema:
    """
    Direct RAG Chain: get_context -> LLM Synthesis.
    Replaces the previous multi-pass ReAct agent for 60% faster retrieval.
    """
    user_input = state["validated_user_input"]

    instruction = state.get("instruction", "")
    weather_info = state.get("weather_info", "")
    
    if DEBUG_MODE:
        print(f"\n=== RETRIVER_AGENT (LINEAR) CALLED ===")
        print(f"User query: {user_input}")
    
    # 1. Get Context (Direct Tool Call)
    context = get_context.func(user_input)


    
    # 2. Prepare Prompt
    llm = get_llm(temperature=0.1)
    
    # Simple direct prompt for faster synthesis
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are a helpful assistant for {ORGANIZATION_NAME}. "
                   "Use the provided context to answer the user question accurately. "
                   "If you don't know the answer based on the context, say 'I don't know'."),
        ("human", "Context:\n{context}\n\nQuestion: {query}\n\n{instruction}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    # 3. Generate Response
    response_str = chain.invoke({
        "context": context,
        "query": user_input,
        "instruction": instruction or "Answer clearly and concisely."
    })

    
    if DEBUG_MODE:
        print(f"Final response preview: {response_str[:100]}...")
        print(f"=== RETRIVER_AGENT COMPLETE ===\n")

    return {
        "query_response": response_str,
        "evaluation_state": "",
        "retry_count": state["retry_count"] + 1,
        "data_source": "retriever",
        "needs_escalation": False
    }


