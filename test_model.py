import asyncio
from src.utils.llm_singleton import get_llm

async def main():
    llm = get_llm()
    print(f"DEBUG: Default model from get_llm(): {llm.model}")
    
    from src.agents.router_agent import router_agent_node
    print("DEBUG: Checking router agent node model...")
    # This might require a state, but we just want to see if it imports/runs
    
    from src.Workflow.master_workflow import model as master_model
    print(f"DEBUG: Master workflow model: {master_model.model}")

if __name__ == "__main__":
    asyncio.run(main())
