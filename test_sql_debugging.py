import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("SUPABASE_DATABASE_URI")
conn = psycopg2.connect(uri)
cursor = conn.cursor()

# Test the exact SQL that was generated
sql = """
SELECT
  tp.name_en,
  tp.name_mr,
  tp.description_en,
  tp.address,
  tp.lat,
  tp.lng,
  tp.image_url
FROM tourist_places AS tp
JOIN districts AS d
  ON tp.district_id = d.id
WHERE
  d.name_en ILIKE '%Gondia%'
LIMIT 10;
"""

print("Executing SQL for Gondia tourist places...")
cursor.execute(sql)
results = cursor.fetchall()

print(f"\nFound {len(results)} results:")
for row in results:
    print(row)

# Test if there's any data in tourist_places
cursor.execute("SELECT COUNT(*) FROM tourist_places;")
total_count = cursor.fetchone()[0]
print(f"\nTotal tourist_places in database: {total_count}")

# Test if there's any matching district
cursor.execute("SELECT id, name_en FROM districts WHERE name_en ILIKE '%Gondia%';")
district = cursor.fetchall()
print(f"\nDistricts matching 'Gondia': {district}")

cursor.close()
conn.close()
