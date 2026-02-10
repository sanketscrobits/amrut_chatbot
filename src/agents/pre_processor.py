import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.agents.weather_enricher import weather_enricher_node
from src.agents.router_agent import router_agent_node
from src.schemas.response_schema import ResponseSchema

async def pre_processor_node(state: ResponseSchema) -> ResponseSchema:
    """
    Async parallel execution of weather and router for better concurrency.
    """
    # 1. Execute weather (sync-ish but fast) and router (async)
    # We use asyncio.to_thread for weather if it's blocking
    weather_task = asyncio.to_thread(weather_enricher_node, state)
    router_task = router_agent_node(state)
    
    # Await both
    weather_result, router_result = await asyncio.gather(weather_task, router_task)
    
    # Merge results
    return {
        "weather_info": weather_result.get("weather_info", ""),
        "data_source": router_result.get("data_source", "retriever")
    }



