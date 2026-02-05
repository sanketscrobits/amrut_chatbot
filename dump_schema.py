import os
import sys
sys.path.append(os.getcwd())
from src.utils.db_connection import get_supabase_db

try:
    print("Connecting to DB to fetch schema...")
    db = get_supabase_db()
    schema = db.get_table_info()
    print("SCHEMA_START")
    print(schema)
    print("SCHEMA_END")
    
    with open("schema_dump.txt", "w") as f:
        f.write(schema)
        
except Exception as e:
    print(f"Error: {e}")
