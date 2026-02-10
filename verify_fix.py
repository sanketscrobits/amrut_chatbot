
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def verify_fix():
    print("Verifying fix with query: 'How many districts are in Maharashtra?'...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chatbot", 
                json={"user_message": "How many districts are in Maharashtra?"}
            )
            data = response.json()
            print("\nResponse Status:", response.status_code)
            print("Escalation Required:", data.get("escalation_required"))
            print("Response Text:\n", data.get("response"))
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(verify_fix())
