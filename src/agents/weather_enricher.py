from langchain_core.messages import HumanMessage, SystemMessage
from src.schemas.response_schema import ResponseSchema
from src.tools.weather_tool import check_weather
from src.utils.llm_singleton import get_llm
from src.settings import DEBUG_MODE

def weather_enricher_node(state: ResponseSchema) -> ResponseSchema:
    """
    Analyzes the user query for locations.
    If a location is found, fetches weather and stores it in weather_info field.
    Weather will be appended to response ONLY when an answer is found.
    """
    user_input = state["validated_user_input"]

    
    # Refined keyword check - only specific weather/location terms
    location_keywords = [
        # Direct weather terms
        "weather", "temperature", "climate", "forecast",
        "rain", "raining", "rainy", "sunny", "cloudy", "storm", "stormy",
        "hot", "cold", "warm", "cool", "humid", "humidity",
        "wind", "windy", "snow", "snowing", "fog", "foggy",
        
        # Weather-related phrases (context-aware)
        "weather in", "temperature in", "climate of", "weather at",
        "how is the weather", "what's the weather", "hows the weather",
        "tell me the weather", "check weather",
        
        # Specific city names (Indian cities commonly queried)
        "gondia", "mumbai", "delhi", "bangalore", "bengaluru", "pune",
        "hyderabad", "chennai", "kolkata", "ahmedabad", "jaipur",
        "lucknow", "nagpur", "indore", "bhopal", "surat", "kanpur"
    ]
    # Removed: "city", "visit", "tourist", "travel", "trip", "destination", "place", "location"
    # These were too generic and caused false positives
    
    has_location_intent = any(keyword in user_input.lower() for keyword in location_keywords)

    
    # Skip weather enrichment entirely if no location-related keywords found
    if not has_location_intent:
        if DEBUG_MODE:
            print("DEBUG: No location keywords detected, skipping weather enrichment")
        return {
            "weather_info": "",  # No weather info
        }

    
    # 1. Location Extraction using LLM (only if keywords detected)
    llm = get_llm(temperature=0)
    messages = [
        SystemMessage(content="Extract the city or tourist location name from the user's query. Return ONLY the name. If no specific physical location is mentioned, return 'None'."),
        HumanMessage(content=user_input)

    ]
    
    weather_info = ""
    try:
        location_response = llm.invoke(messages).content.strip()
        location = location_response.replace('"', '').replace("'", "").replace(".", "")
        
        if location and location.lower() != "none":
            if DEBUG_MODE:
                print(f"Weather Enricher found location: {location}")
            try:
                weather_report = check_weather.invoke(location)
                
                # Check for tool errors or "could not find" messages
                if "Error" not in weather_report and "could not find" not in weather_report.lower():
                    weather_info = weather_report
                    if DEBUG_MODE:
                        print(f"Weather info stored for {location}")
                else:
                    if DEBUG_MODE:
                        print(f"Weather tool could not get data for {location}: {weather_report}")
            except Exception as e:
                print(f"Weather enrichment failed during tool execution: {e}")
        else:
            if DEBUG_MODE:
                print("No location found in query for weather enrichment.")
            
    except Exception as e:
        print(f"Location extraction failed: {e}")
    
    return {
        "weather_info": weather_info,  # Store weather separately
    }

