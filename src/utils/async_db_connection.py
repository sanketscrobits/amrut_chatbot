"""
Async Database Connection Module
Provides non-blocking database operations for better concurrency and performance.
"""

from typing import Optional
import os
import time
import re
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

class AsyncSupabaseDB:
    """Async connection pooled Supabase database for non-blocking operations."""
    
    _instance: Optional["AsyncSupabaseDB"] = None
    _db: Optional[SQLDatabase] = None
    _engine = None
    _async_engine: Optional[AsyncEngine] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_async_engine(self) -> AsyncEngine:
        """Get async engine for non-blocking database operations."""
        if self._async_engine is None:
            from settings import SUPABASE_DATABASE_URI
            
            if not SUPABASE_DATABASE_URI:
                raise ValueError("SUPABASE_DATABASE_URI not set in environment")
            
            # Convert to async URI
            connection_uri = SUPABASE_DATABASE_URI.replace("postgres://", "postgresql+asyncpg://")
            connection_uri = connection_uri.replace("postgresql://", "postgresql+asyncpg://")
            
            # Remove unsupported 'supa' parameter
            if "supa=" in connection_uri:
                connection_uri = re.sub(r'[?&]supa=[^&]+', '', connection_uri)
                if "?" not in connection_uri and "&" in connection_uri:
                    connection_uri = connection_uri.replace("&", "?", 1)
            
            # Get pool configuration
            pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
            max_overflow = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))
            pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
            pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
            
            try:
                print(f"[ASYNC_DB] Initializing async connection pool")
                t0 = time.time()
                
                # Create async SQLAlchemy engine
                self._async_engine = create_async_engine(
                    connection_uri,
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_timeout=pool_timeout,
                    pool_recycle=pool_recycle,
                    pool_pre_ping=True,
                    echo=False
                )
                
                elapsed = time.time() - t0
                print(f"[ASYNC_DB] Async database pool initialized in {elapsed:.2f}s")
                
            except Exception as e:
                raise ConnectionError(f"Failed to create async connection pool: {str(e)}")
        
        return self._async_engine
    
    def get_database(self) -> SQLDatabase:
        """Get synchronous database (kept for backward compatibility)."""
        if self._db is None:
            from settings import SUPABASE_DATABASE_URI
            
            if not SUPABASE_DATABASE_URI:
                raise ValueError("SUPABASE_DATABASE_URI not set in environment")
            
            connection_uri = SUPABASE_DATABASE_URI.replace("postgres://", "postgresql://")
            if "supa=" in connection_uri:
                connection_uri = re.sub(r'[?&]supa=[^&]+', '', connection_uri)
                if "?" not in connection_uri and "&" in connection_uri:
                    connection_uri = connection_uri.replace("&", "?", 1)
            
            pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
            max_overflow = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))
            pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
            pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
            
            try:
                print(f"[DB_POOL] Initializing connection pool (size={pool_size}, max_overflow={max_overflow})")
                t0 = time.time()
                
                self._engine = create_engine(
                    connection_uri,
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_timeout=pool_timeout,
                    pool_recycle=pool_recycle,
                    pool_pre_ping=True,
                    echo=False
                )
                
                self._db = SQLDatabase(
                    engine=self._engine,
                    include_tables=[]
                )
                
                elapsed = time.time() - t0
                print(f"[DB_POOL] Database pool initialized in {elapsed:.2f}s")
                
            except Exception as e:
                raise ConnectionError(f"Failed to create connection pool: {str(e)}")
        
        return self._db

async def get_async_db():
    """Get async database engine for non-blocking operations."""
    return await AsyncSupabaseDB().get_async_engine()

def get_supabase_db() -> SQLDatabase:
    """Get synchronous database (kept for backward compatibility)."""
    return AsyncSupabaseDB().get_database()


# Example async query execution
async def execute_async_query(query: str):
    """
    Execute a SQL query asynchronously.
    
    Example usage:
        result = await execute_async_query("SELECT * FROM tourist_places LIMIT 10")
    """
    engine = await get_async_db()
    
    async with engine.connect() as conn:
        result = await conn.execute(query)
        return result.fetchall()
