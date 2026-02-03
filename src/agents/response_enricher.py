"""
Response Enricher - Appends weather info to response only when an answer was found.
"""
import re
from src.schemas.response_schema import ResponseSchema


def format_weather_naturally(weather_info: str) -> str:
    """
    Convert raw weather data into natural, conversational language.
    """
    if not weather_info or "couldn't find" in weather_info.lower():
        return ""
    
    try:
        # Extract weather components using regex
        condition_match = re.search(r"Condition:\s*([^•\n]+)", weather_info)
        temp_match = re.search(r"Temperature:\s*([\d.]+)°C", weather_info)
        feels_like_match = re.search(r"Feels like:\s*([\d.]+)°C", weather_info)
        humidity_match = re.search(r"Humidity:\s*(\d+)%", weather_info)
        wind_match = re.search(r"Wind Speed:\s*([\d.]+)\s*m/s", weather_info)
        
        condition = condition_match.group(1).strip() if condition_match else "pleasant"
        temp = float(temp_match.group(1)) if temp_match else None
        humidity = int(humidity_match.group(1)) if humidity_match else None
        wind = float(wind_match.group(1)) if wind_match else None
        
        # Build natural language description
        parts = []
        
        # Weather condition description
        condition_lower = condition.lower()
        if "clear" in condition_lower:
            parts.append("the weather is clear with sunny skies")
        elif "cloud" in condition_lower:
            parts.append("it's partly cloudy")
        elif "rain" in condition_lower:
            parts.append("there might be some rain")
        elif "fog" in condition_lower or "mist" in condition_lower:
            parts.append("it's a bit misty")
        else:
            parts.append(f"the weather is {condition.lower()}")
        
        # Temperature
        if temp:
            if temp > 35:
                parts.append(f"and quite hot at around {temp:.0f}°C")
            elif temp > 28:
                parts.append(f"and warm at around {temp:.0f}°C")
            elif temp > 20:
                parts.append(f"with a pleasant temperature of around {temp:.0f}°C")
            elif temp > 10:
                parts.append(f"and a bit cool at around {temp:.0f}°C")
            else:
                parts.append(f"and cold at around {temp:.0f}°C")
        
        # Humidity advice
        if humidity:
            if humidity > 80:
                parts.append("It's quite humid, so stay hydrated and wear light clothing")
            elif humidity > 60:
                parts.append("There's moderate humidity in the air")
        
        # Wind advice
        if wind and wind > 8:
            parts.append("Expect some wind, so you might want to bring a light jacket")
        
        # Combine into natural sentence
        if parts:
            result = "Currently, " + parts[0]
            if len(parts) > 1:
                result += " " + parts[1]
            if len(parts) > 2:
                result += ". " + ". ".join(parts[2:])
            result += "."
            return result
        
        return ""
    except Exception as e:
        print(f"Error formatting weather: {e}")
        return ""


def response_enricher_node(state: ResponseSchema) -> ResponseSchema:
    """
    Appends weather_info to query_response ONLY if an answer was found.
    Formats weather info in natural, conversational language.
    """
    query_response = state.get("query_response", "")
    weather_info = state.get("weather_info", "")
    
    # Only append weather if we have both response and weather
    if query_response and weather_info:
        natural_weather = format_weather_naturally(weather_info)
        if natural_weather:
            enriched_response = f"{query_response}\n\n{natural_weather}"
            print(f"DEBUG: Response enriched with natural weather info")
        else:
            enriched_response = query_response
    else:
        enriched_response = query_response
    
    return {
        "user_query": state["user_query"],
        "query_response": enriched_response,
        "evaluation_state": state.get("evaluation_state", ""),
        "retry_count": state.get("retry_count", 0),
        "instruction": state.get("instruction", ""),
        "data_source": state.get("data_source", ""),
        "weather_info": weather_info,
        "needs_escalation": state.get("needs_escalation", False)
    }
