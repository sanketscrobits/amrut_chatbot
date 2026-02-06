#!/usr/bin/env python3
"""
Comprehensive SQL Agent Test Suite
Tests various query patterns against the chatbot API
"""
import requests
import json
import time
from typing import Dict, List

API_URL = "http://localhost:8000/chatbot"

# Test queries organized by category
TEST_QUERIES = {
    "1. Basic Retrieval": [
        "Show me all tourist places.",
        "List the names of all tourist places available.",
    ],
    
    "2. Filtering & Conditions": [
        "Show tourist places located in Pune.",
        "List tourist places in Mumbai.",
        "Find tourist places in Gondia.",
    ],
    
    "3. Aggregation & Analytics": [
        "How many tourist places are there in total?",
        "How many districts are in the database?",
    ],
    
    "4. Comparison & Ranking": [
        "Show the top 5 tourist places.",
        "List the first 10 tourist places.",
    ],
    
    "5. Location Queries": [
        "Find tourist places near Pune.",
        "Show tourist places in Maharashtra.",
    ],
    
    "6. Edge Cases": [
        "Show tourist places in a city that doesn't exist.",
        "List tourist places in Delhi.",  # Likely no data
    ],
}

def test_query(query: str, category: str) -> Dict:
    """Send a query to the chatbot API and return results"""
    print(f"\n{'='*80}")
    print(f"Category: {category}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    start_time = time.time()
    try:
        response = requests.post(
            API_URL,
            json={"user_message": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            escalation = data.get("escalation_required", False)
            
            print(f"✅ SUCCESS ({duration:.2f}s)")
            print(f"Escalation Required: {escalation}")
            print(f"Response Preview: {response_text[:200]}...")
            
            return {
                "status": "success",
                "duration": duration,
                "escalation": escalation,
                "response_length": len(response_text),
                "has_data": "I don't know" not in response_text
            }
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        duration = time.time() - start_time
        print(f"⏱️ TIMEOUT after {duration:.2f}s")
        return {
            "status": "timeout",
            "duration": duration
        }
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return {
            "status": "exception",
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("SQL AGENT COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    results = {}
    total_tests = sum(len(queries) for queries in TEST_QUERIES.values())
    current_test = 0
    
    for category, queries in TEST_QUERIES.items():
        category_results = []
        
        for query in queries:
            current_test += 1
            print(f"\n[Test {current_test}/{total_tests}]")
            
            result = test_query(query, category)
            category_results.append({
                "query": query,
                "result": result
            })
            
            # Small delay between queries
            time.sleep(1)
        
        results[category] = category_results
    
    # Print summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for category, category_results in results.items():
        print(f"\n{category}")
        print("-" * 80)
        
        success_count = sum(1 for r in category_results if r["result"].get("status") == "success")
        has_data_count = sum(1 for r in category_results if r["result"].get("has_data", False))
        
        print(f"Total: {len(category_results)}")
        print(f"Success: {success_count}/{len(category_results)}")
        print(f"With Data: {has_data_count}/{len(category_results)}")
        
        # Show individual results
        for item in category_results:
            query_short = item["query"][:50] + "..." if len(item["query"]) > 50 else item["query"]
            result = item["result"]
            
            if result.get("status") == "success":
                data_indicator = "✅ DATA" if result.get("has_data") else "⚠️ NO DATA"
                print(f"  • {query_short}: {data_indicator} ({result.get('duration', 0):.2f}s)")
            else:
                print(f"  • {query_short}: ❌ {result.get('status', 'unknown').upper()}")
    
    # Overall stats
    all_results = [r for cat in results.values() for r in cat]
    total_success = sum(1 for r in all_results if r["result"].get("status") == "success")
    total_with_data = sum(1 for r in all_results if r["result"].get("has_data", False))
    
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    print(f"Total Tests: {len(all_results)}")
    print(f"Successful: {total_success}/{len(all_results)} ({100*total_success/len(all_results):.1f}%)")
    print(f"With Data: {total_with_data}/{len(all_results)} ({100*total_with_data/len(all_results):.1f}%)")
    
    # Average duration for successful queries
    successful_durations = [r["result"]["duration"] for r in all_results if r["result"].get("duration")]
    if successful_durations:
        avg_duration = sum(successful_durations) / len(successful_durations)
        print(f"Average Response Time: {avg_duration:.2f}s")

if __name__ == "__main__":
    main()
