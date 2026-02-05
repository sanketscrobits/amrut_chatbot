"""
Direct test of query_tool to verify Weaviate retrieval  
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.tools.query_tool import get_context

print("="*80)
print("DIRECT QUERY_TOOL TEST")
print("="*80)

test_queries = [
    "What are the key features of AMRUT system?",
    "What is the contact information for AMRUT support?",
    "Tell me about the patient care workflow"
]

for i, query in enumerate(test_queries, 1):
    print(f"\n\n{'='*80}")
    print(f"TEST QUERY {i}: {query}")
    print(f"{'='*80}")
    
    # get_context is a StructuredTool, so we need to invoke it properly
    result = get_context.invoke({"query_text": query})
    
    print(f"\n{'='*80}")
    print(f"RESULT:")
    print(result if result else "[EMPTY - NO RESULT]")
    print(f"{'='*80}\n")

print("\n" + "="*80)
print("DIRECT TEST COMPLETE")
print("="*80)
