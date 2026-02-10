
import asyncio
import json
from src.agents.supabase_mcp_agent import supabase_mcp_client

async def inspect_data():
    print("--- Inspecting Table Data ---")
    async with supabase_mcp_client() as session:
        await session.initialize()
        
        # 4. Check Linkage for Pune
        pune_id = "992ba295-5454-4e76-8c2c-d1029ea39965"
        print(f"\n[DEBUG] Checking Emergency Services for Pune ID: {pune_id}...")
        
        # Check count of all services for Pune
        sql_count = f"SELECT COUNT(*) as total_services FROM emergency_services WHERE district_id = '{pune_id}';"
        res_count = await session.call_tool("execute_sql", arguments={"query": sql_count})
        print(f"Total Services for Pune:\n{res_count.content[0].text}")
        
        # Check specific Hospital entries for Pune
        sql_hospitals = f"SELECT name, service_type FROM emergency_services WHERE district_id = '{pune_id}' AND service_type = 'Hospital';"
        res_hosp = await session.call_tool("execute_sql", arguments={"query": sql_hospitals})
        print(f"Hospitals in Pune:\n{res_hosp.content[0].text}")

if __name__ == "__main__":
    asyncio.run(inspect_data())
