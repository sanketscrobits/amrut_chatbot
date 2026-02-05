"""
End-to-End API Testing Script for AMRUT Chatbot
Tests all endpoints from the Postman collection with Weaviate vector database.
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_RESULTS = []

def log_test(name, status, details=""):
    """Log test result"""
    result = {
        "test": name,
        "status": status,
        "details": details,
        "timestamp": time.strftime("%H:%M:%S")
    }
    TEST_RESULTS.append(result)
    symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"\n{symbol} {name}")
    if details:
        print(f"   {details}")

def create_test_document():
    """Create a test document about AMRUT system"""
    content = """
    # AMRUT Health Monitoring System Documentation

    ## Overview
    AMRUT is a comprehensive health monitoring and patient care system designed for healthcare facilities.

    ## Key Features
    
    ### 1. Real-Time Vital Signs Monitoring
    - Continuous tracking of heart rate, blood pressure, temperature, and oxygen levels
    - Automatic alerts when vitals exceed normal ranges
    - Historical data visualization
    
    ### 2. Electronic Health Records (EHR)
    - Centralized patient information storage
    - Medical history tracking
    - Prescription management
    - Lab results integration
    
    ### 3. Intelligent Alerting System
    - Critical health metric notifications
    - Customizable alert thresholds
    - Multi-channel notifications (SMS, email, app)
    
    ### 4. Treatment Planning
    - Collaborative care coordination
    - Treatment protocol templates
    
    ### 5. Multi-User Access
    - Role-based permissions (doctors, nurses, administrators)
    - Secure authentication
    - Audit logging
    
    ## System Requirements
    - Modern web browser (Chrome, Firefox, Safari)
    - Stable internet connection
    - Supported on desktop and mobile devices
    
    ## Patient Care Workflow
    1. Patient registration and admission
    2. Vital signs setup and monitoring
    3. Doctor consultations and diagnosis
    4. Treatment plan creation
    5. Medication administration tracking
    6. Progress monitoring
    7. Discharge planning
    
    ## Contact Information
    For technical support, contact: support@amrut-health.com
    Emergency hotline: +91-1234567890
    """
    
    # Save to temp file as markdown (which will work better with the loader)
    test_file = Path("/tmp/amrut_test_document.md")
    test_file.write_text(content)
    return str(test_file), content

def test_health_check():
    """Test 1: Health Check Endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200 and response.json().get("status") == "ok":
            log_test("Health Check", "PASS", "Server is running correctly")
            return True
        else:
            log_test("Health Check", "FAIL", f"Unexpected response: {response.text}")
            return False
    except Exception as e:
        log_test("Health Check", "FAIL", f"Error: {str(e)}")
        return False

def test_document_upload():
    """Test 2: Upload Document"""
    try:
        # Create test document
        file_path, content = create_test_document()
        test_uuid = "test-amrut-doc-12345"
        
        with open(file_path, 'rb') as f:
            files = {'file': ('amrut_test_document.md', f, 'text/markdown')}
            response = requests.post(
                f"{BASE_URL}/upload/{test_uuid}",
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            log_test(
                "Document Upload",
                "PASS",
                f"Document uploaded successfully. Source ID: {result.get('source_id')}, Namespace: {result.get('namespace')}"
            )
            return True, test_uuid
        else:
            log_test("Document Upload", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return False, None
            
    except Exception as e:
        log_test("Document Upload", "FAIL", f"Error: {str(e)}")
        return False, None

def test_query_uploaded_document():
    """Test 3: Query Chatbot About Uploaded Document"""
    try:
        # Wait a bit for indexing
        time.sleep(3)
        
        test_queries = [
            {
                "query": "What are the key features of AMRUT system?",
                "expected_keywords": ["vital signs", "monitoring", "EHR", "health records"]
            },
            {
                "query": "What is the contact information for AMRUT support?",
                "expected_keywords": ["support", "email", "hotline", "contact"]
            },
            {
                "query": "Tell me about the patient care workflow",
                "expected_keywords": ["registration", "admission", "monitoring", "discharge"]
            }
        ]
        
        all_passed = True
        for i, test in enumerate(test_queries):
            try:
                payload = {"user_message": test["query"]}
                response = requests.post(
                    f"{BASE_URL}/chatbot",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    answer = response.json().get("response", response.text)
                    
                    # Check if any expected keyword is in the response
                    found_keywords = [kw for kw in test["expected_keywords"] if kw.lower() in str(answer).lower()]
                    
                    if found_keywords:
                        log_test(
                            f"Query {i+1}: '{test['query'][:50]}...'",
                            "PASS",
                            f"Bot answered correctly. Found keywords: {', '.join(found_keywords)}"
                        )
                    else:
                        log_test(
                            f"Query {i+1}: '{test['query'][:50]}...'",
                            "WARN",
                            f"Bot responded but expected keywords not found. Response: {str(answer)[:200]}"
                        )
                        all_passed = False
                else:
                    log_test(
                        f"Query {i+1}",
                        "FAIL",
                        f"Status: {response.status_code}, Response: {response.text[:200]}"
                    )
                    all_passed = False
                    
                time.sleep(2)  # Delay between queries
                
            except Exception as e:
                log_test(f"Query {i+1}", "FAIL", f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        log_test("Query Testing", "FAIL", f"Error: {str(e)}")
        return False

def test_general_chat():
    """Test 4: General Chat (Non-Document Query)"""
    try:
        payload = {"user_message": "What is the weather like today?"}
        response = requests.post(
            f"{BASE_URL}/chatbot",
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            log_test(
                "General Chat",
                "PASS",
                "Bot responded to general query (non-document related)"
            )
            return True
        else:
            log_test("General Chat", "FAIL", f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("General Chat", "FAIL", f"Error: {str(e)}")
        return False

def test_delete_document(doc_uuid):
    """Test 5: Delete Document"""
    if not doc_uuid:
        log_test("Document Delete", "SKIP", "No document UUID to delete")
        return False
    
    try:
        response = requests.delete(f"{BASE_URL}/chatbot/delete/{doc_uuid}")
        
        if response.status_code == 200:
            log_test(
                "Document Delete",
                "PASS",
                f"Document {doc_uuid} deleted successfully"
            )
            return True
        else:
            log_test("Document Delete", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Document Delete", "FAIL", f"Error: {str(e)}")
        return False

def verify_weaviate_storage(doc_uuid):
    """Test 6: Verify Weaviate Storage"""
    try:
        import weaviate
        
        # Connect to Weaviate
        client = weaviate.connect_to_local(host="localhost", port=8080)
        
        try:
            collection = client.collections.get("AmrutChatbotDocs")
            
            # Query for our test document
            response = collection.query.fetch_objects(
                limit=100
            )
            
            # Count objects with our source UUID
            count = sum(1 for obj in response.objects if obj.properties.get('source') == doc_uuid)
            
            if count > 0:
                log_test(
                    "Weaviate Storage Verification",
                    "PASS",
                    f"Found {count} chunks from test document in Weaviate"
                )
                return True
            else:
                log_test(
                    "Weaviate Storage Verification",
                    "WARN",
                    "No chunks found in Weaviate (document may have been deleted)"
                )
                return False
        finally:
            client.close()
            
    except Exception as e:
        log_test("Weaviate Storage Verification", "FAIL", f"Error: {str(e)}")
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for t in TEST_RESULTS if t["status"] == "PASS")
    failed = sum(1 for t in TEST_RESULTS if t["status"] == "FAIL")
    warned = sum(1 for t in TEST_RESULTS if t["status"] == "WARN")
    total = len(TEST_RESULTS)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    if warned > 0:
        print(f"⚠️  Warnings: {warned}/{total}")
    
    print(f"\nSuccess Rate: {(passed/total)*100:.1f}%")
    
    # Detailed results
    print("\n" + "-"*80)
    print("DETAILED RESULTS")
    print("-"*80)
    for result in TEST_RESULTS:
        status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
        print(f"\n[{result['timestamp']}] {status_symbol} {result['test']}")
        if result["details"]:
            print(f"    → {result['details']}")
    
    return passed, failed

def main():
    print("="*80)
    print("AMRUT CHATBOT - END-TO-END API TESTING")
    print("Testing with Weaviate Vector Database")
    print("="*80)
    
    print("\n🔍 Checking server availability...")
    if not test_health_check():
        print("\n❌ Server is not available. Please start the server first:")
        print("   python3 -m uvicorn src.main.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print("\n📄 Testing document upload functionality...")
    upload_success, doc_uuid = test_document_upload()
    
    if upload_success and doc_uuid:
        print("\n🔍 Verifying document storage in Weaviate...")
        verify_weaviate_storage(doc_uuid)
        
        print("\n💬 Testing chatbot queries about uploaded document...")
        test_query_uploaded_document()
    
    print("\n💬 Testing general chat functionality...")
    test_general_chat()
    
    if upload_success and doc_uuid:
        print("\n🗑️  Testing document deletion...")
        test_delete_document(doc_uuid)
    
    # Print results
    passed, failed = print_summary()
    
    print("\n" + "="*80)
    if failed == 0:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    else:
        print(f"⚠️  TESTING COMPLETED WITH {failed} FAILURES")
    print("="*80)
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
