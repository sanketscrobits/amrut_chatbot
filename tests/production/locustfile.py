"""
Locust load testing scenarios for AMRUT Chatbot
Simulates realistic user behavior under load
"""
from locust import HttpUser, task, between
import random
import tempfile
import os

# Sample documents for upload testing
SAMPLE_DOCS = {
    "policy": "# Policy\n\nThis is a sample policy document with important information.",
    "guide": "# User Guide\n\nStep-by-step instructions for using the system.",
    "faq": "# FAQ\n\nFrequently asked questions and answers.",
}

SAMPLE_QUERIES = [
    "What is the policy about data privacy?",
    "How do I get started?",
    "What are the system requirements?",
    "Who can I contact for support?",
    "What are the main features?",
    "How do I upload documents?",
    "What is the pricing?",
    "Is there a mobile app?",
]


class ChatbotUser(HttpUser):
    """Simulates a typical chatbot user"""
    
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        self.user_id = f"user_{random.randint(1000, 9999)}"
        self.uploaded_docs = []
    
    @task(5)  # Weight: 50% of actions are queries
    def query_chatbot(self):
        """Send a query to the chatbot"""
        query = random.choice(SAMPLE_QUERIES)
        
        with self.client.post(
            "/chatbot",
            json={"user_message": query},
            catch_response=True,
            name="Query Chatbot"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if 'response' in data:
                    response.success()
                else:
                    response.failure("No response in JSON")
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(3)  # Weight: 30% of actions are uploads
    def upload_document(self):
        """Upload a document"""
        doc_name = random.choice(list(SAMPLE_DOCS.keys()))
        doc_content = SAMPLE_DOCS[doc_name]
        doc_id = f"{self.user_id}_{doc_name}_{len(self.uploaded_docs)}"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(doc_content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': (f'{doc_name}.md', f, 'text/markdown')}
                
                with self.client.post(
                    f"/upload/{doc_id}",
                    files=files,
                    catch_response=True,
                    name="Upload Document"
                ) as response:
                    if response.status_code == 200:
                        self.uploaded_docs.append(doc_id)
                        response.success()
                    else:
                        response.failure(f"Got status {response.status_code}")
        finally:
            os.unlink(temp_path)
    
    @task(2)  # Weight: 20% of actions are deletes
    def delete_document(self):
        """Delete a previously uploaded document"""
        if not self.uploaded_docs:
            return  # Nothing to delete
        
        doc_id = random.choice(self.uploaded_docs)
        
        with self.client.delete(
            f"/chatbot/delete/{doc_id}",
            catch_response=True,
            name="Delete Document"
        ) as response:
            if response.status_code == 200:
                self.uploaded_docs.remove(doc_id)
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(1)  # Weight: 10% of actions are health checks
    def health_check(self):
        """Check if server is healthy"""
        with self.client.get("/", catch_response=True, name="Health Check") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class HeavyUser(HttpUser):
    """Simulates a heavy user with more frequent actions"""
    
    wait_time = between(1, 2)  # Faster actions
    
    @task
    def rapid_queries(self):
        """Send multiple rapid queries"""
        for _ in range(3):
            query = random.choice(SAMPLE_QUERIES)
            self.client.post("/chatbot", json={"user_message": query}, name="Rapid Query")


# Run with:
# locust -f tests/production/locustfile.py --host=http://localhost:8000
# Then open http://localhost:8089 for web UI
