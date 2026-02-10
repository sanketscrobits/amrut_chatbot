from src.schemas.response_schema import ResponseSchema
import asyncio

# OPTIMIZATION Phase 2: Query Expansion for better RAG recall
from src.utils.query_expansion import expand_query_smart
from settings import GOOGLE_API_KEY, ORGANIZATION_NAME, DEBUG_MODE
from src.utils.llm_singleton import get_llm
from src.tools.query_tool import get_context
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

async def retriver_agent(state: ResponseSchema) -> ResponseSchema:
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
    
    # OPTIMIZATION Phase 2: Query Expansion for better RAG recall
    # Generate 2-3 semantic variations to improve document matching
    query_variations = expand_query_smart(user_input)
    
    if DEBUG_MODE and len(query_variations) > 1:
        print(f"🔍 Query expansion: Generated {len(query_variations)} variations")
        for i, variant in enumerate(query_variations):
            if i > 0:  # Skip original
                print(f"  Variant {i}: {variant}")
    
    # 1. Get Context with query expansion
    # Try original query first, then fall back to expansions if needed
    context = await asyncio.to_thread(get_context.func, user_input)
    
    # If context is too short and we have expansions, try combining results
    if len(str(context)) < 200 and len(query_variations) > 1:
        # Context seems sparse, try getting more with variations
        expanded_contexts = [context]
        for variant in query_variations[1:2]:  # Try 1 more variation
            variant_context = await asyncio.to_thread(get_context.func, variant)
            if variant_context and variant_context not in expanded_contexts:
                expanded_contexts.append(variant_context)
        
        # Combine unique contexts
        context = "\n\n---\n\n".join([str(c) for c in expanded_contexts if c])
        
        if DEBUG_MODE:
            print(f"📚 Combined context from {len(expanded_contexts)} queries ({len(str(context))} chars)")

    # 2. Prepare Prompt
    llm = get_llm(model="gemini-2.5-flash", temperature=0.1)
    
    # Simple direct prompt for faster synthesis
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are a helpful assistant for {ORGANIZATION_NAME}. "
                   "Use the provided context to answer the user question accurately. "
                   "If you don't know the answer based on the context, say 'I don't know'."),
        ("human", "Context:\n{context}\n\nQuestion: {query}\n\n{instruction}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    # 3. Generate Response
    response_str = await chain.ainvoke({
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


