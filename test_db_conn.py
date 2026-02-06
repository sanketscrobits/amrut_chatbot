import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Project specific info from .env
project_id = "xvrpudtkpgsjbaogqamh"
password = "uqmlpUGqJfw68WTG"

# Alternative Host (Pooler)
alt_host = "aws-0-ap-south-1.pooler.supabase.com"
user = f"postgres.{project_id}"

# Test 1: ap-south-1 pooler with SSL variants
region = "ap-south-1"
host = f"aws-0-{region}.pooler.supabase.com"
print(f"Testing {host} with SSL variants...")

for port in [6543, 5432]:
    for user_fmt in [f"postgres.{project_id}", "postgres"]:
        for ssl in ["require", "disable"]:
            try:
                print(f"Trying: port={port}, user={user_fmt}, ssl={ssl}...")
                conn = psycopg2.connect(
                    host=host, 
                    port=port, 
                    user=user_fmt, 
                    password=password, 
                    database="postgres", 
                    sslmode=ssl,
                    connect_timeout=10
                )
                print(f"!!! SUCCESS: port={port}, user={user_fmt}, ssl={ssl}")
                conn.close()
                exit(0)
            except Exception as e:
                print(f"FAILED: {e}")

