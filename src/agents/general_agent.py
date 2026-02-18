from src.schemas.response_schema import ResponseSchema
from src.utils.llm_singleton import get_llm
from src.settings import ORGANIZATION_NAME, DEBUG_MODE
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def general_agent_node(state: ResponseSchema) -> ResponseSchema:
    """
    Respond to general/conversational queries using the LLM directly.
    No database or vector store lookup is performed.
    """
    user_input = state["validated_user_input"]

    if DEBUG_MODE:
        print(f"\n=== GENERAL AGENT CALLED ===")
        print(f"User query: {user_input}")

    llm = get_llm(temperature=0.3)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "CRITICAL LANGUAGE RULE: You MUST respond in the EXACT SAME language as the user's message. "
         "If the user writes in English, reply in English. "
         "If the user writes in Marathi, reply in Marathi. "
         "If the user writes in Hindi, reply in Hindi. "
         "NEVER switch languages unless the user does.\n\n"
         f"You are a friendly and helpful AI assistant for {ORGANIZATION_NAME}. "
         "You assist users with questions about Maharashtra tourism, local services, "
         "uploaded documents, and general conversation.\n\n"
         "RULES:\n"
         "1. For greetings, respond warmly and briefly mention how you can help.\n"
         "2. For capability questions, describe what you can do: answer questions about "
         "tourist places, districts, local businesses, emergency services, weather, "
         "and uploaded documents.\n"
         "3. For general knowledge questions, answer concisely using your training data.\n"
         "4. Keep responses concise and helpful.\n"
         "5. Do NOT make up specific data about Maharashtra places or services — "
         "those queries should be handled by the database."),
        ("human", "{query}")
    ])

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({"query": user_input})

    if DEBUG_MODE:
        print(f"General response preview: {response[:100]}...")
        print(f"=== GENERAL AGENT COMPLETE ===\n")

    return {
        "query_response": response.strip(),
        "data_source": "general",
        "needs_escalation": False
    }
