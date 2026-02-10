from dotenv import load_dotenv
from os import getenv
from pathlib import Path

load_dotenv(".env")

BASE_DIR = Path(__file__).resolve().parent.parent

GOOGLE_API_KEY=getenv("GEMINI_API_KEY")
GEMINI_API_KEY=GOOGLE_API_KEY
PINECONE_API_KEY=getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME=getenv("PINECONE_INDEX_NAME")
PINECONE_REGION=getenv("PINECONE_REGION")
PINECONE_HOST=getenv("PINECONE_HOST")
WHATSAPP_TOKEN=getenv("WA_ACCESS_TOKEN")
PHONE_NUMBER_ID=getenv("WA_PHONE_NUMBER_ID")
GUARDRAILS_API_KEY=getenv("GUARDRAILS_API_KEY")
ORGANIZATION_NAME = getenv("ORGANIZATION_NAME")

# Supabase Database Configuration
SUPABASE_DATABASE_URI = getenv("SUPABASE_DATABASE_URI")
SUPABASE_DB_HOST = getenv("SUPABASE_DB_HOST")
SUPABASE_DB_PORT = getenv("SUPABASE_DB_PORT", "5432")
SUPABASE_DB_NAME = getenv("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = getenv("SUPABASE_DB_USER")
SUPABASE_DB_PASSWORD = getenv("SUPABASE_DB_PASSWORD")

# Weather Configuration
OPENWEATHER_API_KEY = getenv("OPENWEATHER_API_KEY")

# Weaviate Vector Database Configuration
WEAVIATE_URL = getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = getenv("WEAVIATE_API_KEY", None)  # Optional for local instances
WEAVIATE_COLLECTION_NAME = getenv("WEAVIATE_COLLECTION_NAME", "AmrutChatbotDocs")

# Vector Database Selection
VECTOR_DB_TYPE = getenv("VECTOR_DB_TYPE", "weaviate")  # "pinecone" or "weaviate"

NAMESPACE = getenv("NAMESPACE")

# Performance & Debugging Configuration
DEBUG_MODE = True