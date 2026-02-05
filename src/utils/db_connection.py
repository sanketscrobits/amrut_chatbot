from typing import Optional
from langchain_community.utilities import SQLDatabase

class SupabaseDBSingleton:
    """Singleton for Supabase database connection."""
    
    _instance: Optional["SupabaseDBSingleton"] = None
    _db: Optional[SQLDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_database(self) -> SQLDatabase:
        if self._db is None:
            # Lazy import to avoid circular dependencies
            from settings import SUPABASE_DATABASE_URI
            
            if not SUPABASE_DATABASE_URI:
                raise ValueError("SUPABASE_DATABASE_URI not set in environment")
            
            # Fix deprecated schema and remove unsupported 'supa' parameter
            connection_uri = SUPABASE_DATABASE_URI.replace("postgres://", "postgresql://")
            if "supa=" in connection_uri:
                import re
                connection_uri = re.sub(r'[?&]supa=[^&]+', '', connection_uri)
                # If we removed the initial ?, make sure the first param starts with ? if any exist
                if "?" not in connection_uri and "&" in connection_uri:
                    connection_uri = connection_uri.replace("&", "?", 1)
            
            try:
                self._db = SQLDatabase.from_uri(connection_uri)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
                
        return self._db

def get_supabase_db() -> SQLDatabase:
    """Helper function to get the Supabase database instance."""
    return SupabaseDBSingleton().get_database()
