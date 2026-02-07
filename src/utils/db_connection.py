from typing import Optional
import os
import time
import re
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class SupabaseDBPooled:
    """Connection pooled Supabase database for better performance."""
    
    _instance: Optional["SupabaseDBPooled"] = None
    _db: Optional[SQLDatabase] = None
    _engine = None
    
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
                connection_uri = re.sub(r'[?&]supa=[^&]+', '', connection_uri)
                # If we removed the initial ?, make sure the first param starts with ? if any exist
                if "?" not in connection_uri and "&" in connection_uri:
                    connection_uri = connection_uri.replace("&", "?", 1)
            
            # Get pool configuration from environment with sensible defaults
            pool_size = int(os.getenv("DB_POOL_SIZE", "2"))  # Reduced default from 5
            max_overflow = int(os.getenv("DB_POOL_MAX_OVERFLOW", "15"))  # Increased from 10
            pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "10"))
            pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 min instead of 1 hour
            pool_pre_ping = os.getenv("DB_POOL_PRE_PING", "false").lower() == "true"
            
            try:
                print(f"[DB_POOL] Initializing connection pool (size={pool_size}, max_overflow={max_overflow}, pre_ping={pool_pre_ping})")
                t0 = time.time()
                
                # Create SQLAlchemy engine with connection pooling
                self._engine = create_engine(
                    connection_uri,
                    poolclass=QueuePool,
                    pool_size=pool_size,           # Minimum connections to keep
                    max_overflow=max_overflow,     # Maximum additional connections
                    pool_timeout=pool_timeout,      # Wait timeout for connection
                    pool_recycle=pool_recycle,      # Recycle connections after 30 min
                    pool_pre_ping=pool_pre_ping,    # Disabled by default for speed (was causing 17s delays!)
                    echo=False                      # Don't log SQL queries
                )
                
                # Create LangChain SQLDatabase with our pooled engine
                # CRITICAL FIX: Skip ALL metadata reflection for instant initialization
                # - include_tables=[]  : Don't reflect any tables (we provide schema manually)
                # - sample_rows_in_table_info=0 : Don't sample rows (expensive!)
                # - view_support=False : Don't query for views
                # This brings init time from 14s → <1s!
                self._db = SQLDatabase(
                    engine=self._engine,
                    include_tables=[],              # Don't reflect tables
                    sample_rows_in_table_info=0,    # Don't sample rows (MAJOR SPEEDUP!)
                    view_support=False               # Don't query views
                )
                
                elapsed = time.time() - t0
                print(f"[DB_POOL] Database pool initialized in {elapsed:.2f}s")
                print(f"[DB_POOL] Pool status: {self._engine.pool.size()} connections, {self._engine.pool.checkedout()} checked out")
                
            except Exception as e:
                raise ConnectionError(f"Failed to create connection pool: {str(e)}")
                
        return self._db
    
    def get_pool_status(self):
        """Get current pool status for monitoring"""
        if self._engine:
            return {
                "pool_size": self._engine.pool.size(),
                "checked_out": self._engine.pool.checkedout(),
                "overflow": self._engine.pool.overflow(),
                "total_connections": self._engine.pool.size() + self._engine.pool.overflow()
            }
        return None

def get_supabase_db() -> SQLDatabase:
    """Helper function to get the pooled Supabase database instance."""
    return SupabaseDBPooled().get_database()

def get_db_pool_status():
    """Get current database pool status for monitoring"""
    return SupabaseDBPooled().get_pool_status()
