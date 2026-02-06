import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("SUPABASE_DATABASE_URI")
print(f"Testing connection with URI: {uri[:50]}...")

try:
    conn = psycopg2.connect(uri)
    print("✅ SUCCESS: Connected to Supabase via Pooler!")
    
    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM districts;")
    count = cursor.fetchone()[0]
    print(f"✅ Query test passed. Found {count} districts in the database.")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ FAILED: {e}")
