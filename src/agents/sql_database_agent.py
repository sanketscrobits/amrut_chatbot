"""
SQL Database Agent using SQLDatabaseToolkit

This agent can query the Supabase PostgreSQL database using natural language.
It uses LangChain's SQLDatabaseToolkit for database interaction.
The connection and LLM are managed via singletons to improve performance and avoid circular imports.
"""

import os
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from src.utils.db_connection import get_supabase_db
from src.utils.llm_singleton import get_llm
from src.utils.yaml_loader import load_prompts

def create_sql_agent(model: str = "gemini-2.5-flash", temperature: float = 0):
    """
    Create a SQL database agent that can query Supabase.
    Uses singletons for database connection and LLM.
    """
    # Get singleton instance
    llm = get_llm(model=model, temperature=temperature)
    db = get_supabase_db()
    
    # Create toolkit with all SQL tools
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    # Load prompt from YAML
    # Path relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "..", "utils", "prompts.yml")
    prompts = load_prompts(prompts_path)
    system_prompt = prompts.get("sql_agent_prompt", "You are an agent designed to interact with a SQL database.")

    # Create and return the agent
    agent = create_agent(llm, tools, system_prompt=system_prompt)
    return agent


def query_database(question: str, agent=None):
    """
    Query the database using natural language.
    """
    if agent is None:
        agent = create_sql_agent()
    
    # LangGraph react agent uses 'messages' input
    result = agent.invoke({"messages": [("user", question)]})
    content = result["messages"][-1].content
    
    # If the response is a list (multimodal/block format), extract the text components
    if isinstance(content, list):
        full_text = ""
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                full_text += part.get("text", "")
            elif isinstance(part, str):
                full_text += part
        return full_text.strip()
        
    return content.strip() if hasattr(content, 'strip') else content


if __name__ == "__main__":
    print("Testing Structured SQL Database Agent...")
    print("-" * 50)
    
    # Test query
    question = "tell me the tourist highlights in gondia?"
    print(f"Question: {question}")
    print("-" * 50)
    
    try:
        response = query_database(question)
        print(f"Answer: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")
