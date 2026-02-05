"""
Example: Using Weaviate Vector Database

This example demonstrates how to use the WeaviateVectorIndex implementation
with the VectorStoreSingleton for document ingestion and querying.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.vector_db.index_strategies.weaviate_vector_index import WeaviateVectorIndex
from src.utils.vector_db.vector_store_singleton import VectorStoreSingleton
from src.utils.vector_db.loader_strategies.base import DocumentLoaderStrategy


# Dummy document loader for this example
class SimpleDocumentLoader(DocumentLoaderStrategy):
    def load_document(self, file_path: str) -> str:
        with open(file_path, 'r') as f:
            return f.read()


def main():
    print("=" * 80)
    print("WEAVIATE VECTOR DATABASE EXAMPLE")
    print("=" * 80)
    
    # 1. Initialize embeddings model
    print("\n[1] Initializing embeddings model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    print("✓ Embeddings model loaded")
    
    # 2. Create Weaviate vector index instance
    print("\n[2] Creating Weaviate vector index...")
    vector_index = WeaviateVectorIndex(embeddings=embeddings)
    print("✓ Weaviate vector index created")
    print("  Note: Make sure Weaviate is running (e.g., via Docker)")
    print("  Docker command: docker run -d -p 8080:8080 -p 50051:50051 semitechnologies/weaviate:latest")
    
    # 3. Initialize VectorStoreSingleton
    print("\n[3] Initializing VectorStoreSingleton...")
    document_loader = SimpleDocumentLoader()
    vector_store = VectorStoreSingleton(
        embeddings_model=embeddings,
        document_loader_strategy=document_loader,
        vector_index_strategy=vector_index
    )
    print("✓ VectorStoreSingleton initialized with Weaviate")
    
    # 4. Ingest a sample document
    print("\n[4] Ingesting sample document...")
    sample_text = """
    AMRUT is a comprehensive health monitoring system designed to track patient vitals,
    medical history, and treatment plans. The system provides real-time alerts for
    critical health metrics and enables healthcare providers to make informed decisions.
    
    Key features include:
    - Real-time vital signs monitoring
    - Electronic health records management
    - Intelligent alerting system
    - Multi-user access with role-based permissions
    """
    
    namespace = "example_namespace"
    source = "sample_doc_001"
    
    vector_store.ingest_document(
        text=sample_text,
        namespace=namespace,
        source=source
    )
    print(f"✓ Document ingested (namespace: {namespace}, source: {source})")
    
    # 5. Perform semantic search
    print("\n[5] Performing semantic search...")
    query = "What are the key features of AMRUT?"
    results = vector_store.query(query, namespace=namespace)
    print(f"\nQuery: {query}")
    print(f"Results:\n{results}")
    
    # 6. Delete the document
    print("\n[6] Cleaning up - deleting document...")
    vector_store.delete_document(source=source, namespace=namespace)
    print(f"✓ Document deleted (source: {source})")
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
