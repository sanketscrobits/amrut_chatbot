
import asyncio
import httpx
import time
import json
import statistics
from dataclasses import dataclass
from typing import List, Optional, Any

BASE_URL = "http://localhost:8000"

@dataclass
class TestCase:
    name: str
    endpoint: str
    method: str
    payload: Optional[dict] = None
    expected_status: int = 200
    description: str = ""

TEST_CASES = [
    # 1. Health Check
    TestCase(
        name="Health Check",
        endpoint="/",
        method="GET",
        description="Verify API is up and running"
    ),
    
    # 2. Hard SQL Questions (Supabase MCP)
    TestCase(
        name="SQL: Highest Population District",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "Which district has the highest population?"},
        description="Aggregation/Sorting: Requires finding max value in districts table."
    ),
    TestCase(
        name="SQL: Tourist Places in Pune",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "List all tourist places in Pune district."},
        description="Filtering/Join: Requires filtering tourist_places by district name."
    ),
    TestCase(
        name="SQL: Total District Population",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "What is the total population of all districts combined?"},
        description="Aggregation: Summing a column across all rows."
    ),
    TestCase(
        name="SQL: Count Tourist Places",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "How many tourist places are there in total?"},
        description="Aggregation: Counting rows in tourist_places table."
    ),
    TestCase(
        name="SQL: Top 3 Largest Districts",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "What are the top 3 items in the districts table by area? List their names."},
        description="Sorting/Limit: Ordering and limiting results."
    ),
    TestCase(
        name="SQL: Negative/Non-existent",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "Tell me about the Atlantis district."},
        description="Negative Case: Should handle missing data gracefully."
    ),
     TestCase(
        name="SQL: Complex Condition",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "List districts with population greater than 2 million and sort them alphabetically."},
        description="Filtering/Sorting: Multiple conditions."
    ),

    # 3. Escalation/Router Check
    TestCase(
        name="Escalation: Crypto Price",
        endpoint="/chatbot",
        method="POST",
        payload={"user_message": "What is the price of bitcoin today?"},
        description="Router Logic: Should route to escalation/general knowledge or fail safely."
    ),
    
    # 4. Admin Check (State dependent, just checking endpoint reachability)
    TestCase(
        name="Admin: List Active Escalations",
        endpoint="/admin/escalations/active",
        method="GET",
        description="Endpoint Verify: Admin route reachability."
    )
]

async def run_test(client: httpx.AsyncClient, case: TestCase) -> dict:
    print(f"Running: {case.name}...")
    start_time = time.time()
    try:
        if case.method == "GET":
            response = await client.get(f"{BASE_URL}{case.endpoint}", timeout=30.0)
        elif case.method == "POST":
            response = await client.post(f"{BASE_URL}{case.endpoint}", json=case.payload, timeout=30.0)
        else:
            return {"status": "SKIPPED", "latency": 0, "error": "Method not supported"}
            
        latency = time.time() - start_time
        
        result = {
            "name": case.name,
            "description": case.description,
            "latency": latency,
            "status_code": response.status_code,
            "success": response.status_code == case.expected_status,
            "response_preview": response.text[:200].replace('\n', ' ') if response.text else "Empty"
        }
        
    except Exception as e:
        latency = time.time() - start_time
        result = {
            "name": case.name,
            "description": case.description,
            "latency": latency,
            "status_code": 0,
            "success": False,
            "response_preview": f"Error: {str(e)}"
        }
        
    return result

async def main():
    print(f"Starting E2E Performance Test against {BASE_URL}...\n")
    
    results = []
    async with httpx.AsyncClient() as client:
        # Warmup
        await client.get(f"{BASE_URL}/")
        
        for case in TEST_CASES:
            res = await run_test(client, case)
            results.append(res)
            # Small delay between requests
            await asyncio.sleep(0.5)
            
    # Generate Report
    print("\n\n" + "="*80)
    print(f"{'TEST CASE':<35} | {'STATUS':<8} | {'LATENCY (s)':<12} | {'RESPONSE PREVIEW'}")
    print("-" * 80)
    
    latencies = []
    failures = 0
    
    report_md = "# E2E Chatbot Performance Report\n\n"
    report_md += "| Test Case | Description | Status | Latency (s) | Response Preview |\n"
    report_md += "|---|---|---|---|---|\n"

    for r in results:
        status_icon = "✅" if r['success'] else "❌"
        if r['success']:
            latencies.append(r['latency'])
        else:
            failures += 1
            
        print(f"{r['name']:<35} | {r['status_code']:<8} | {r['latency']:.4f}       | {r['response_preview']}")
        
        # Markdown row
        clean_preview = r['response_preview'].replace("|", "\|")
        report_md += f"| {r['name']} | {r['description']} | {status_icon} {r['status_code']} | {r['latency']:.4f} | {clean_preview} |\n"

    avg_latency = statistics.mean(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    
    summary = f"\n\n## Summary\n"
    summary += f"- **Total Tests**: {len(results)}\n"
    summary += f"- **Passed**: {len(results) - failures}\n"
    summary += f"- **Failed**: {failures}\n"
    summary += f"- **Avg Latency**: {avg_latency:.4f}s\n"
    summary += f"- **Max Latency**: {max_latency:.4f}s\n"
    
    report_md += summary
    print(summary)
    
    with open("tests/e2e_report.md", "w") as f:
        f.write(report_md)
    print("\nFull report saved to tests/e2e_report.md")

if __name__ == "__main__":
    asyncio.run(main())
