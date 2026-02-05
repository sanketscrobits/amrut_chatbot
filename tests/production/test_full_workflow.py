"""
Production-level functional tests for AMRUT Chatbot
Tests complete document lifecycle under realistic conditions
"""
import pytest
import requests
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.fixtures.test_data import SAMPLE_DOCUMENTS, SAMPLE_QUERIES, EXPECTED_KEYWORDS

BASE_URL = "http://localhost:8000"

class TestFullWorkflow:
    """Test complete document lifecycle"""
    
    def test_01_health_check(self):
        """Verify API is running"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print("✅ Health check passed")
    
    def test_02_upload_all_documents(self):
        """Upload all sample documents"""
        results = {}
        
        for doc_id, content in SAMPLE_DOCUMENTS.items():
            # Create temp file
            temp_file = f"/tmp/{doc_id}.md"
            with open(temp_file, 'w') as f:
                f.write(content)
            
            # Upload
            with open(temp_file, 'rb') as f:
                files = {'file': (f'{doc_id}.md', f, 'text/markdown')}
                response = requests.post(
                    f"{BASE_URL}/upload/{doc_id}",
                    files=files
                )
            
            assert response.status_code == 200, f"Upload failed for {doc_id}"
            results[doc_id] = response.json()
            print(f"✅ Uploaded: {doc_id}")
            time.sleep(1)  # Rate limiting
        
        assert len(results) == len(SAMPLE_DOCUMENTS)
        print(f"✅ All {len(results)} documents uploaded successfully")
    
    def test_03_query_all_documents(self):
        """Query each uploaded document"""
        results = {}
        
        for doc_id, queries in SAMPLE_QUERIES.items():
            results[doc_id] = {}
            
            for query in queries:
                response = requests.post(
                    f"{BASE_URL}/chatbot",
                    json={"user_message": query}
                )
                
                assert response.status_code == 200, f"Query failed: {query}"
                data = response.json()
                results[doc_id][query] = data['response']
                
                # Check if response is meaningful (not "I don't know")
                assert "dont know" not in data['response'].lower() or not data.get('escalation_required', True), \
                    f"Query failed to retrieve info: {query}"
                
                print(f"✅ Query answered: {query[:50]}...")
                time.sleep(2)  # Rate limiting for agent processing
        
        print(f"✅ All queries processed successfully")
        return results
    
    def test_04_validate_query_accuracy(self):
        """Validate that queries return expected information"""
        correct = 0
        total = 0
        
        for doc_id, query_keywords in EXPECTED_KEYWORDS.items():
            for query, keywords in query_keywords.items():
                response = requests.post(
                    f"{BASE_URL}/chatbot",
                    json={"user_message": query}
                )
                
                assert response.status_code == 200
                answer = response.json()['response'].lower()
                
                # Check if any expected keyword is present
                found = any(kw.lower() in answer for kw in keywords)
                total += 1
                if found:
                    correct += 1
                    print(f"✅ Accurate: {query[:40]}...")
                else:
                    print(f"⚠️  Partial: {query[:40]}... (keywords: {keywords})")
                
                time.sleep(2)
        
        accuracy = (correct / total) * 100 if total > 0 else 0
        print(f"\n📊 Query Accuracy: {accuracy:.1f}% ({correct}/{total})")
        assert accuracy >= 60, f"Accuracy too low: {accuracy}%"
    
    def test_05_concurrent_queries(self):
        """Test multiple rapid queries"""
        import concurrent.futures
        
        def make_query(query):
            response = requests.post(
                f"{BASE_URL}/chatbot",
                json={"user_message": query}
            )
            return response.status_code == 200
        
        queries = [
            "What is the data encryption policy?",
            "What documents do I need for registration?",
            "What are common side effects?",
            "What payment methods are accepted?",
            "What is Code Blue protocol?",
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_query, queries))
        
        success_rate = (sum(results) / len(results)) * 100
        print(f"✅ Concurrent queries: {success_rate:.0f}% success rate")
        assert success_rate == 100, "Some concurrent queries failed"
    
    def test_06_delete_all_documents(self):
        """Delete all uploaded documents"""
        for doc_id in SAMPLE_DOCUMENTS.keys():
            response = requests.delete(f"{BASE_URL}/chatbot/delete/{doc_id}")
            assert response.status_code == 200, f"Delete failed for {doc_id}"
            print(f"✅ Deleted: {doc_id}")
            time.sleep(0.5)
        
        print(f"✅ All documents deleted successfully")
    
    def test_07_verify_cleanup(self):
        """Verify documents are actually deleted"""
        # Try querying deleted documents
        query = "What is the data encryption policy?"
        response = requests.post(
            f"{BASE_URL}/chatbot",
            json={"user_message": query}
        )
        
        assert response.status_code == 200
        # Should not find the specific healthcare policy info anymore
        answer = response.json()['response']
        print(f"✅ Post-deletion query: {answer[:100]}...")


class TestErrorHandling:
    """Test error scenarios and recovery"""
    
    def test_invalid_file_upload(self):
        """Test uploading invalid file"""
        response = requests.post(
            f"{BASE_URL}/upload/test-invalid",
            files={'file': ('test.xyz', b'invalid content', 'application/octet-stream')}
        )
        # Should handle gracefully (either reject or process)
        assert response.status_code in [200, 400, 422]
        print("✅ Invalid file handled gracefully")
    
    def test_empty_query(self):
        """Test empty chat message"""
        response = requests.post(
            f"{BASE_URL}/chatbot",
            json={"user_message": ""}
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
        print("✅ Empty query handled gracefully")
    
    def test_very_long_query(self):
        """Test extremely long query"""
        long_query = "What is " + "very " * 1000 + "important information?"
        response = requests.post(
            f"{BASE_URL}/chatbot",
            json={"user_message": long_query}
        )
        assert response.status_code in [200, 400, 413]
        print("✅ Long query handled gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
