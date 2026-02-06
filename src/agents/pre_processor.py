import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.agents.weather_enricher import weather_enricher_node
from src.agents.router_agent import router_agent_node
from src.schemas.response_schema import ResponseSchema

async def pre_processor_node_async(state: ResponseSchema) -> ResponseSchema:
    """
    FIX #2: Async parallel execution of weather and router for better concurrency.
    Uses asyncio instead of direct ThreadPoolExecutor to avoid conflicts with FastAPI.
    """
    loop = asyncio.get_event_loop()
    
    # Execute weather and router in parallel using executor
    with ThreadPoolExecutor(max_workers=2) as executor:
        weather_task = loop.run_in_executor(executor, weather_enricher_node, state)
        router_task = loop.run_in_executor(executor, router_agent_node, state)
        
        # Await both tasks
        weather_result, router_result = await asyncio.gather(weather_task, router_task)
    
    # Merge results
    return {
        "weather_info": weather_result.get("weather_info", ""),
        "data_source": router_result.get("data_source", "retriever")
    }

def pre_processor_node(state: ResponseSchema) -> ResponseSchema:
    """
    Synchronous wrapper for async preprocessing.
    Maintains compatibility with existing synchronous workflow.
    """
    # Check if we're in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context but need to run sync
        # Fall back to simple ThreadPoolExecutor for now
        with ThreadPoolExecutor(max_workers=2) as executor:
            weather_future = executor.submit(weather_enricher_node, state)
            router_future = executor.submit(router_agent_node, state)
            
            weather_result = weather_future.result()
            router_result = router_future.result()
        
        return {
            "weather_info": weather_result.get("weather_info", ""),
            "data_source": router_result.get("data_source", "retriever")
        }
    except RuntimeError:
        # No event loop running, we can create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(pre_processor_node_async(state))
            return result
        finally:
            loop.close()



