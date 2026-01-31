from langchain_core.messages import HumanMessage, SystemMessage
from src.schemas.response_schema import ResponseSchema
from src.tools.weather_tool import check_weather
from src.utils.llm_singleton import get_llm

def weather_enricher_node(state: ResponseSchema) -> ResponseSchema:
    """
    Analyzes the user query for locations.
    If a location is found, fetches weather and appends it to instructions.
    """
    user_query = state["user_query"]
    current_instruction = state.get("instruction", "")
    
    # 1. Simple Location Extraction using LLM
    # We use a lower temperature for deterministic extraction
    llm = get_llm(temperature=0)
    messages = [
        SystemMessage(content="Extract the city or tourist location name from the user's query. Return ONLY the name. If no specific physical location is mentioned, return 'None'."),
        HumanMessage(content=user_query)
    ]
    
    try:
        location_response = llm.invoke(messages).content.strip()
        # Remove any surrounding quotes or punctuation provided by LLM
        location = location_response.replace('"', '').replace("'", "").replace(".", "")
        
        weather_info = ""
        # Check if a valid location was found (ignore 'None' or empty)
        if location and location.lower() != "none":
            print(f"DEBUG: Weather Enricher found location: {location}")
            # Get weather using the tool
            try:
                # Invoke the tool directly
                weather_report = check_weather.invoke(location)
                
                # Check for tool errors or "could not find" messages
                if "Error" not in weather_report and "could not find" not in weather_report.lower():
                    weather_info = f"\n\n[Context: {weather_report}]"
                    print(f"DEBUG: Weather info found for {location}")
                else:
                    print(f"DEBUG: Weather tool could not get data for {location}: {weather_report}")
            except Exception as e:
                print(f"Weather enrichment failed during tool execution: {e}")
        else:
            print("DEBUG: No location found in query for weather enrichment.")
            
    except Exception as e:
        print(f"Location extraction failed: {e}")
        weather_info = ""
            
    # Append to instruction
    new_instruction = f"{current_instruction}{weather_info}".strip()
    
    return {
        "user_query": user_query,
        "query_response": "", # Not answering yet
        "evaluation_state": "",
        "retry_count": state.get("retry_count", 0),
        "instruction": new_instruction,
        "data_source": ""
    }
