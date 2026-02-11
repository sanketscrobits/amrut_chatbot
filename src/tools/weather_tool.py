import os
import requests
import re
from typing import Optional, Tuple, Dict, Any, List
from langchain.tools import tool
from src.utils.db_connection import get_supabase_db

class WeatherTool:
    def __init__(self, api_key: Optional[str] = None):
        # Ensure env vars are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        # Lazy import to avoid circular dependencies if settings imports this file
        try:
            from src.settings import OPENWEATHER_API_KEY
            self.api_key = api_key or OPENWEATHER_API_KEY
        except ImportError:
            self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        
        if not self.api_key:
            # Try getting directly from env as fallback
            self.api_key = os.getenv("OPENWEATHER_API_KEY")
            
        if not self.api_key:
            print("Warning: OPENWEATHER_API_KEY not set in environment or settings.")

    def get_coordinates_from_supabase(self, location_name: str) -> Optional[Tuple[float, float]]:
        """
        Query Supabase to get latitude and longitude for a location.
        """
        try:
            db = get_supabase_db()
            
            # Sanitize input roughly to prevent simple injection if not parameterized
            # SQLDatabase.run typically takes raw SQL. 
            # Ideally we should use parameterization if supported by the underlying driver via run logic
            # or just be careful. For now, we'll strip special chars.
            clean_location = location_name.replace("'", "").replace(";", "").strip()
            
            # Construct query to find location case-insensitively
            query = f"SELECT lat, lng FROM districts WHERE name_en ILIKE '%{clean_location}%' LIMIT 1"
            
            # Execute query
            print(f"DEBUG: Executing query: {query}")
            # db.run returns the string representation of the result
            result_str = db.run(query) 
            print(f"DEBUG: Query result: {result_str}")
            
            if not result_str or result_str == "[]":
                print(f"Location '{location_name}' not found in Supabase.")
                return None
                
            # Parse the string result - handle Decimal objects by extracting numbers
            # Result format: "[(Decimal('16.91'), Decimal('72.61'))]" or "[(16.91, 72.61)]"
            try:
                # Extract all numbers (including decimals) from the result string
                numbers = re.findall(r"[-+]?\d*\.?\d+", result_str)
                if len(numbers) >= 2:
                    lat = float(numbers[0])
                    lon = float(numbers[1])
                    print(f"DEBUG: Found coords: {lat}, {lon}")
                    return lat, lon
            except Exception as parse_error:
                print(f"Error parsing DB result '{result_str}': {parse_error}")
                return None
                
            return None
            
        except Exception as e:
            print(f"Error executing Supabase query for coordinates: {e}")
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
        # We strip the location to handle cases like "Pune "
        coords = tool_instance.get_coordinates_from_supabase(location.strip())
        
        if not coords:
            # Fallback: We could return a message asking for specific coordinates or 
            # maybe the location is just not in our tourist database.
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
