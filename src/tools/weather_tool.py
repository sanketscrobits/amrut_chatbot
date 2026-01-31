import os
import requests
import ast
import re
from typing import Optional, Tuple, Dict, Any, List
from langchain.tools import tool
from src.agents.sql_database_agent import create_sql_agent

class WeatherTool:
    def __init__(self, api_key: Optional[str] = None):
        # Ensure env vars are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        # Lazy import to avoid circular dependencies if settings imports this file
        try:
            from settings import OPENWEATHER_API_KEY
            self.api_key = api_key or OPENWEATHER_API_KEY
        except ImportError:
            self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        
        if not self.api_key:
            # Try getting directly from env as fallback
            self.api_key = os.getenv("OPENWEATHER_API_KEY")
            
        if not self.api_key:
            print("Warning: OPENWEATHER_API_KEY not set in environment or settings.")
            
        # Initialize SQL Agent for coordinate lookup
        self.sql_agent = create_sql_agent()

    def get_coordinates_from_supabase(self, location_name: str) -> Optional[Tuple[float, float]]:
        """
        Query Supabase to get latitude and longitude for a location using the SQL Agent.
        """
        try:
            # Ask the SQL agent to find coordinates
            query = f"What are the latitude and longitude coordinates for {location_name}? Return only the numbers."
            
            # Invoke the agent
            result = self.sql_agent.invoke({"messages": [("user", query)]})
            content = result["messages"][-1].content
            
            # Handle list content (multimodal) if necessary
            text_response = ""
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_response += part.get("text", "")
                    elif isinstance(part, str):
                        text_response += part
            else:
                text_response = str(content)
                
            print(f"DEBUG: SQL Agent Response for coords: {text_response}")
            
            # Verify if the response contains "don't know" or similar failure
            if "don't know" in text_response.lower() or "no information" in text_response.lower():
                return None
                
            # Extract numbers using regex
            # Looking for patterns like (21.46, 80.19) or just two float numbers
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", text_response)
            
            if len(numbers) >= 2:
                # Assuming first two numbers are lat and lon
                lat = float(numbers[0])
                lon = float(numbers[1])
                print(f"DEBUG: Parsed coords: {lat}, {lon}")
                return lat, lon
            
            return None
            
        except Exception as e:
            print(f"Error fetching coordinates from Supabase via SQL Agent: {e}")
            return None

    def get_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch weather data from OpenWeatherMap."""
        if not self.api_key:
            raise ValueError("OpenWeather API key is not configured.")
            
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch weather data: {e}")

@tool
def check_weather(location: str) -> str:
    """
    Check the current weather for a specific location.
    The tool first looks up the location's coordinates availability in the internal database.
    
    Args:
        location: Name of the city or place (e.g., "Gondia", "Tadoba", "Pune")
    """
    try:
        tool_instance = WeatherTool()
        
        # 1. Try to get coordinates from Supabase
        coords = tool_instance.get_coordinates_from_supabase(location.strip())
        
        if not coords:
            return f"I couldn't find the location '{location}' in our database to get its coordinates. Please try another location."
            
        lat, lon = coords
        
        # 2. Get weather info
        weather_data = tool_instance.get_weather(lat, lon)
        
        # 3. Format the response
        main = weather_data.get('weather', [{}])[0].get('main', 'Unknown')
        desc = weather_data.get('weather', [{}])[0].get('description', 'Unknown')
        temp = weather_data.get('main', {}).get('temp', 'Unknown')
        feels_like = weather_data.get('main', {}).get('feels_like', 'Unknown')
        humidity = weather_data.get('main', {}).get('humidity', 'Unknown')
        wind_speed = weather_data.get('wind', {}).get('speed', 'Unknown')
        
        return (f"Current Weather in {location.title()} (Lat: {lat}, Lon: {lon}):\n"
                f"• Condition: {main} ({desc.capitalize()})\n"
                f"• Temperature: {temp}°C (Feels like: {feels_like}°C)\n"
                f"• Humidity: {humidity}%\n"
                f"• Wind Speed: {wind_speed} m/s")
                
    except Exception as e:
        return f"Error checking weather: {str(e)}"
