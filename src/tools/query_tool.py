from langchain.tools import tool
from src.utils.vector_db.vector_store_singleton import VectorStoreSingleton
from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.vector_db.loader_strategies.local_loader import LocalLoader
from src.utils.vector_db.vector_store_factory import create_vector_store
from settings import NAMESPACE, DEBUG_MODE

# Cache vector store instance to avoid recreation on every call
_vector_store_cache = None

def _get_or_create_vector_store():
    """Get cached vector store or create new one if needed."""
    global _vector_store_cache
    
    if _vector_store_cache is None:
        if DEBUG_MODE:
            print("Initializing vector store cache (first call)...")
        embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        document_loader_strategy = LocalLoader()
        vector_index_strategy = create_vector_store(embeddings=embeddings_model)
        
        _vector_store_cache = VectorStoreSingleton(
            embeddings_model=embeddings_model,
            document_loader_strategy=document_loader_strategy,
            vector_index_strategy=vector_index_strategy,
        )
    
    return _vector_store_cache


@tool
def get_context(query_text: str) -> str:
    """
    This function helps to answer user question by retrieving relevant context from documents.
    
    Args: 
        query_text: User question in string format
        
    Returns: 
        Context related to user's question in string format
    """
    if DEBUG_MODE:
        print(f"\n=== GET_CONTEXT CALLED ===")
        print(f"Query: {query_text}")
        print(f"Namespace: {NAMESPACE}")

    # Use cached vector store
    vector_store = _get_or_create_vector_store()

    result = vector_store.query(query_text=query_text, namespace=NAMESPACE)
    if DEBUG_MODE:
        print(f"Result length: {len(result) if result else 0}")
        print(f"Result preview: {result[:200] if result else 'EMPTY'}...")
        print(f"=== GET_CONTEXT COMPLETE ===\n")
    return result

if __name__ == "__main__":
    print(get_context("What initiative did the federal government announce regarding AI?"))