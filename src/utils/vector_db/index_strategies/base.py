from abc import ABC, abstractmethod

class VectorIndexStrategy(ABC):

    @abstractmethod
    def create_or_load_vector_index(self, markdown_text: str, chunker=None, namespace: str = None, source: str = "uploaded_file"):
        """
        Create or load a vector index from markdown text.
        
        Args:
            markdown_text: The markdown text to index
            chunker: Optional callable to chunk the text
            namespace: Optional namespace for multi-tenancy
            source: Identifier for the source document
        """
        pass

    @abstractmethod
    def semantic_search(self, embeded_query: list[float], namespace: str = None) -> str:
        """
        Perform semantic search using an embedded query.
        
        Args:
            embeded_query: The embedded query vector
            namespace: Optional namespace to search within
            
        Returns:
            The most relevant context string
        """
        pass
    
    @abstractmethod
    def delete_by_source(self, source: str, namespace: str = None):
        """
        Delete all vectors matching the source metadata field.
        
        Args:
            source: The source identifier to delete
            namespace: Optional namespace to delete from
        """
        pass
