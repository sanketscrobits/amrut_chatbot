from langchain.tools import tool
from src.utils.vector_db.vector_store_singleton import VectorStoreSingleton
from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.vector_db.loader_strategies.local_loader import LocalLoader
from src.utils.vector_db.vector_store_factory import create_vector_store
from settings import NAMESPACE


@tool
def get_context(query_text: str) -> str:
    """
    This function helps to answer user question by retrieving relevant context from documents.
    
    Args: 
        query_text: User question in string format
        
    Returns: 
        Context related to user's question in string format
    """
    print(f"\n=== GET_CONTEXT CALLED ===")
    print(f"Query: {query_text}")
    print(f"Namespace: {NAMESPACE}")

    embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    document_loader_strategy = LocalLoader()
    # Use factory pattern to create vector store based on VECTOR_DB_TYPE setting
    vector_index_strategy = create_vector_store(embeddings=embeddings_model)

    vector_store = VectorStoreSingleton(
        embeddings_model=embeddings_model,
        document_loader_strategy=document_loader_strategy,
        vector_index_strategy=vector_index_strategy,
    )

    result = vector_store.query(query_text = query_text, namespace=NAMESPACE)
    print(f"Result length: {len(result) if result else 0}")
    print(f"Result preview: {result[:200] if result else 'EMPTY'}...")
    print(f"=== GET_CONTEXT COMPLETE ===\n")
    return result

if __name__ == "__main__":
    print(get_context("What initiative did the federal government announce regarding AI?"))