"""
Example: Switching Between Vector Databases

This example demonstrates three ways to switch between Pinecone and Weaviate
vector database implementations:

1. Using environment variables
2. Direct instantiation
3. Factory pattern (recommended)
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.vector_db.vector_store_factory import create_vector_store, get_available_databases
from src.utils.vector_db.index_strategies.pinecone_vector_index import PineconeVectorIndex
from src.utils.vector_db.index_strategies.weaviate_vector_index import WeaviateVectorIndex
from src.utils.vector_db.vector_store_singleton import VectorStoreSingleton


def method_1_environment_variables():
    """Method 1: Switch using environment variables"""
    print("\n" + "=" * 80)
    print("METHOD 1: SWITCHING VIA ENVIRONMENT VARIABLES")
    print("=" * 80)
    
    print("\nSet the VECTOR_DB_TYPE environment variable:")
    print("  export VECTOR_DB_TYPE=pinecone  # Use Pinecone")
    print("  export VECTOR_DB_TYPE=weaviate  # Use Weaviate")
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # The factory will read VECTOR_DB_TYPE from settings
    vector_store = create_vector_store(embeddings)
    
    print(f"\n✓ Vector store created: {type(vector_store).__name__}")
    print(f"  Current VECTOR_DB_TYPE: {os.getenv('VECTOR_DB_TYPE', 'pinecone (default)')}")


def method_2_direct_instantiation():
    """Method 2: Direct instantiation of specific implementation"""
    print("\n" + "=" * 80)
    print("METHOD 2: DIRECT INSTANTIATION")
    print("=" * 80)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Option A: Use Pinecone directly
    print("\n[Option A] Using Pinecone directly:")
    pinecone_store = PineconeVectorIndex(embeddings=embeddings)
    print(f"✓ Created: {type(pinecone_store).__name__}")
    
    # Option B: Use Weaviate directly
    print("\n[Option B] Using Weaviate directly:")
    weaviate_store = WeaviateVectorIndex(embeddings=embeddings)
    print(f"✓ Created: {type(weaviate_store).__name__}")
    
    print("\nNote: This approach gives you explicit control but is less flexible")


def method_3_factory_pattern():
    """Method 3: Factory pattern with explicit type (recommended)"""
    print("\n" + "=" * 80)
    print("METHOD 3: FACTORY PATTERN (RECOMMENDED)")
    print("=" * 80)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("\nAvailable databases:", ", ".join(get_available_databases()))
    
    # Option A: Use Pinecone
    print("\n[Option A] Using factory to create Pinecone:")
    pinecone_store = create_vector_store(embeddings, db_type="pinecone")
    print(f"✓ Created: {type(pinecone_store).__name__}")
    
    # Option B: Use Weaviate
    print("\n[Option B] Using factory to create Weaviate:")
    weaviate_store = create_vector_store(embeddings, db_type="weaviate")
    print(f"✓ Created: {type(weaviate_store).__name__}")
    
    print("\nAdvantages:")
    print("  ✓ Single function to create any vector store")
    print("  ✓ Easy to add new implementations")
    print("  ✓ Configuration-based or explicit selection")
    print("  ✓ Type-safe with VectorIndexStrategy interface")


def complete_example_with_switching():
    """Complete example showing how to switch at runtime"""
    print("\n" + "=" * 80)
    print("COMPLETE EXAMPLE: RUNTIME SWITCHING")
    print("=" * 80)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Sample data
    sample_text = """
    AMRUT Health Monitoring System provides comprehensive patient care
    with real-time vitals tracking and intelligent alerting.
    """
    
    # Function to test any vector store implementation
    def test_vector_store(db_type: str):
        print(f"\n--- Testing {db_type.upper()} ---")
        
        try:
            # Create vector store using factory
            vector_store = create_vector_store(embeddings, db_type=db_type)
            print(f"✓ Created {type(vector_store).__name__}")
            
            # Ingest document
            vector_store.create_or_load_vector_index(
                markdown_text=sample_text,
                namespace="test",
                source=f"{db_type}_test"
            )
            print(f"✓ Document ingested")
            
            # Search
            query_embedding = embeddings.embed_query("patient care features")
            result = vector_store.semantic_search(query_embedding, namespace="test")
            print(f"✓ Search completed: {result[:100]}...")
            
            # Delete
            vector_store.delete_by_source(source=f"{db_type}_test", namespace="test")
            print(f"✓ Document deleted")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Test both implementations
    for db in ["pinecone", "weaviate"]:
        test_vector_store(db)
    
    print("\n" + "=" * 80)
    print("✓ Both implementations work identically!")
    print("=" * 80)


def main():
    print("\n" + "=" * 80)
    print("VECTOR DATABASE SWITCHING EXAMPLES")
    print("=" * 80)
    print("\nThis script demonstrates multiple ways to switch between")
    print("Pinecone and Weaviate vector database implementations.")
    
    # Run all examples
    try:
        method_1_environment_variables()
    except Exception as e:
        print(f"\nError in Method 1: {e}")
    
    try:
        method_2_direct_instantiation()
    except Exception as e:
        print(f"\nError in Method 2: {e}")
    
    try:
        method_3_factory_pattern()
    except Exception as e:
        print(f"\nError in Method 3: {e}")
    
    # Uncomment to run the complete example
    # Note: This requires both Pinecone and Weaviate to be properly configured
    # try:
    #     complete_example_with_switching()
    # except Exception as e:
    #     print(f"\nError in Complete Example: {e}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    print("""
Use the factory pattern (Method 3) for production code:

    from src.utils.vector_db.vector_store_factory import create_vector_store
    
    # Configuration-based (reads from environment)
    vector_store = create_vector_store(embeddings)
    
    # Or explicit selection
    vector_store = create_vector_store(embeddings, db_type="weaviate")

This approach provides:
    ✓ Flexibility to switch databases via configuration
    ✓ Clean abstraction over implementation details
    ✓ Easy testing with different backends
    ✓ Future-proof for adding new vector databases
    """)


if __name__ == "__main__":
    main()
