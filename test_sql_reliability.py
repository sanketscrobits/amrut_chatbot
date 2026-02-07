import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_query(query, expected_category):
    print(f"\nTesting: '{query}'")
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/chatbot",
            json={"user_message": query},
            timeout=30
        )
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            source = data.get("data_source", "unknown")
            escalated = data.get("escalation_required", False)
            answer = data.get("response", "")
            
            status = "✅ PASS" if (source == "sql" and not escalated) else "❌ FAIL"
            if escalated: status += " (Escalated)"
            if source != "sql": status += f" (Source: {source})"
            
            print(f"{status} - {elapsed:.0f}ms")
            print(f"Answer: {answer[:100]}...")
            return source == "sql" and not escalated
        else:
            print(f"❌ FAIL - {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

queries = [
    ("Show me all tourist places", "Basic Retrieval"),
    ("How many tourist places are there in total?", "Aggregation"),
    ("Show the top 5 highest-rated tourist places", "Ranking"),
    ("Show tourist places with missing ratings", "Edge Case"),
    ("Show me a tourist place that doesn't exist", "Edge Case")
]

print("=== SQL RELIABILITY TEST ===")
passed = 0
for q, cat in queries:
    if test_query(q, cat):
        passed += 1

print(f"\nResult: {passed}/{len(queries)} passed")
