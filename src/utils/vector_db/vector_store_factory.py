"""
Factory pattern for creating vector store instances.

This module provides a factory function to instantiate the appropriate
vector database implementation based on configuration.
"""

from src.utils.vector_db.index_strategies.base import VectorIndexStrategy
from settings import VECTOR_DB_TYPE


def create_vector_store(embeddings, db_type: str = None) -> VectorIndexStrategy:
    """
    Create a vector store instance based on the specified database type.
    
    Args:
        embeddings: The embeddings model instance (e.g., HuggingFaceEmbeddings)
        db_type: Optional database type override. If None, uses VECTOR_DB_TYPE from settings.
                 Valid values: "pinecone", "weaviate"
    
    Returns:
        VectorIndexStrategy: An instance of the appropriate vector database implementation
    
    Raises:
        ValueError: If an unsupported database type is specified
    
    Example:
        >>> from langchain_huggingface import HuggingFaceEmbeddings
        >>> embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        >>> 
        >>> # Use default from settings
        >>> vector_store = create_vector_store(embeddings)
        >>> 
        >>> # Override to use Weaviate
        >>> vector_store = create_vector_store(embeddings, db_type="weaviate")
    """
    # Use provided db_type or fall back to settings
    selected_db = (db_type or VECTOR_DB_TYPE).lower()
    
    if selected_db == "pinecone":
        from src.utils.vector_db.index_strategies.pinecone_vector_index import PineconeVectorIndex
        return PineconeVectorIndex(embeddings=embeddings)
    
    elif selected_db == "weaviate":
        from src.utils.vector_db.index_strategies.weaviate_vector_index import WeaviateVectorIndex
        return WeaviateVectorIndex(embeddings=embeddings)
    
    else:
        raise ValueError(
            f"Unsupported vector database type: '{selected_db}'. "
            f"Supported types: 'pinecone', 'weaviate'"
        )


def get_available_databases() -> list[str]:
    """
    Get a list of available vector database implementations.
    
    Returns:
        list[str]: List of supported database type identifiers
    """
    return ["pinecone", "weaviate"]
