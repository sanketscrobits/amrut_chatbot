import time
import sys
import os

# Ensure src is in path
sys.path.append(os.getcwd())

from src.Workflow.workflow import workflow

def test_query(query, expected_source):
    print(f"\nTesting Query: '{query}'")
    print(f"Expected Source: {expected_source}")
    
    start_time = time.time()
    try:
        initial_state = {
            "user_query": query,
            "query_response": "",
            "evaluation_state": "",
            "retry_count": 0,
            "instruction": "",
            "data_source": "",
            "weather_info": "",
            "needs_escalation": False
        }
        
        # Invoke workflow
        final_state = workflow.invoke(initial_state)
        
        end_time = time.time()
        duration = end_time - start_time
        
        source = final_state.get("data_source", "unknown")
        response = final_state.get("query_response", "")[:50] + "..."
        
        print(f"Actual Source: {source}")
        print(f"Response: {response}")
        print(f"Duration: {duration:.4f}s")
        
        if expected_source and source != expected_source:
            print(f"❌ Mismatch! Expected {expected_source}, got {source}")
        else:
            print("✅ Routing Correct")
            
        return duration
        
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    print("=== LATENCY BENCHMARK V2 ===")
    
    # Warm up (Connection + Router load)
    print("Warming up...")
    test_query("hi", "retriever") 
    
    print("\nBENCHMARKING:")
    
    # Test 1: SQL Query
    t1 = test_query("List tourist places in Gondia", "sql")
    
    # Test 2: Retriever Query
    t2 = test_query("How do I register for the portal?", "retriever")
    
    print("\nRESULTS:")
    print(f"SQL Latency: {t1:.4f}s")
    print(f"Retriever Latency: {t2:.4f}s")
    
    if t1 < 5.0 and t2 < 5.0:
        print("✅ PERFORMANCE TARGET MET (Approx <5s is excellent given local env)")
    else:
        print("⚠️ PERFORMANCE NOTICE: Check timings")
