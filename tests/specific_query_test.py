
import asyncio
import httpx
import time
import json
from dataclasses import dataclass

BASE_URL = "http://localhost:8000"


QUERIES = [
    "Tell me about Pune district",
    "What is the population of Nashik district?",
    "Give a short description of Kolhapur",
    "Best time to visit Aurangabad",
    "What are the tourist attractions in Satara?",
    "Why is Ratnagiri famous?",
    "Where is Solapur district located?",
    "Show me tourist places in Lonavala",
    "Emergency hospitals in Pune",
    "24x7 hospital in Kolhapur",
    "Police station contact number in Nashik",
    "24x7 pharmacy in Aurangabad",
    "Emergency services available in my district",
    "What categories of tourist places are available?",
    "Show all tourism categories",
    "पुणे जिल्ह्याची माहिती द्या",
    "कोल्हापूरला भेट देण्याचा सर्वोत्तम काळ कोणता?",
    "नाशिकमध्ये कोणती पर्यटन स्थळे आहेत?",
    "सोलापूर जिल्ह्याचे वर्णन करा",
    "माझ्या परिसरातील रुग्णालयांची माहिती द्या"
]

async def run_query(client: httpx.AsyncClient, query: str):
    print(f"Querying: '{query}'...")
    start_time = time.time()
    try:
        response = await client.post(
            f"{BASE_URL}/chatbot", 
            json={"user_message": query}, 
            timeout=120.0
        )
        latency = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                "query": query,
                "status": "✅ 200",
                "latency": latency,
                "response": data.get("response", "No response"),
                "escalated": data.get("escalation_required", False)
            }
        else:
             return {
                "query": query,
                "status": f"❌ {response.status_code}",
                "latency": latency,
                "response": response.text,
                "escalated": False
            }
    except Exception as e:
        return {
            "query": query,
            "status": "❌ Error",
            "latency": time.time() - start_time,
            "response": str(e),
            "escalated": False
        }

async def main():
    print(f"Starting Specific Query Test against {BASE_URL}...\n")
    
    results = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Warmup
        await client.get(f"{BASE_URL}/")
        
        for q in QUERIES:
            res = await run_query(client, q)
            results.append(res)
            # Small delay
            await asyncio.sleep(1)
            
    # Generate Report
    print("\n\n" + "="*100)
    print(f"{'QUERY':<40} | {'LATENCY':<8} | {'ESCALATED':<10} | {'RESPONSE PREVIEW'}")
    print("-" * 100)
    
    md_output = "# Specific Query Test Results\n\n| Query | Latency (s) | Escalated | Response |\n|---|---|---|---|\n"
    
    for r in results:
        status_icon = "⚠️" if r['escalated'] else "✅"
        if r['status'] != "✅ 200":
             status_icon = "❌"
             
        preview = r['response'].replace("\n", " ")[:100] + "..." if len(r['response']) > 100 else r['response']
        clean_response = r['response'].replace("\n", "<br>").replace("|", "\|")
        
        print(f"{r['query']:<40} | {r['latency']:.2f}s    | {str(r['escalated']):<10} | {preview}")
        
        md_output += f"| {r['query']} | {r['latency']:.2f} | {status_icon} {r['escalated']} | {clean_response} |\n"
        
    with open("tests/specific_query_report.md", "w") as f:
        f.write(md_output)
    print("\nResults saved to tests/specific_query_report.md")

if __name__ == "__main__":
    asyncio.run(main())
