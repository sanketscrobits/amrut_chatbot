import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("SUPABASE_DATABASE_URI")
conn = psycopg2.connect(uri)
cursor = conn.cursor()

print("=" * 80)
print("SUPABASE DATA INVENTORY")
print("=" * 80)

# Check tourist places distribution by district
cursor.execute("""
SELECT d.name_en, COUNT(tp.id) as count
FROM districts d
LEFT JOIN tourist_places tp ON d.id = tp.district_id
GROUP BY d.name_en
HAVING COUNT(tp.id) > 0
ORDER BY count DESC;
""")

results = cursor.fetchall()
print(f"\n✅ Tourist Places Distribution ({len(results)} districts with data):")
print("-" * 80)
for district, count in results:
    print(f"  {district}: {count} tourist places")

# Total counts
cursor.execute("SELECT COUNT(*) FROM districts;")
total_districts = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM tourist_places;")
total_places = cursor.fetchone()[0]

print(f"\n📊 Overall Statistics:")
print("-" * 80)
print(f"  Total Districts: {total_districts}")
print(f"  Total Tourist Places: {total_places}")
print(f"  Districts with Data: {len(results)}")
print(f"  Districts without Data: {total_districts - len(results)}")

cursor.close()
conn.close()
