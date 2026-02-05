from src.utils.vector_db.loader_strategies.base import DocumentLoaderStrategy
from src.utils.vector_db.index_strategies.base import VectorIndexStrategy
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Fixed import
path = r"F:\\ScroBits_Tech\\Query-Agent\\documents\\MIREMS.pdf"

class VectorStoreSingleton():
    _instance = None

    vector_store = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VectorStoreSingleton, cls).__new__(cls)
        return cls._instance

    def __init__(self, embeddings_model, document_loader_strategy: DocumentLoaderStrategy, vector_index_strategy: VectorIndexStrategy):
        if not hasattr(self, '_initialized'):
            self.embeddings_model = embeddings_model
            self.document_loader_strategy = document_loader_strategy
            self.vector_index_strategy = vector_index_strategy
            
            # Use fixed-size chunking with overlap for better retrieval consistency
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,  # Fixed size for consistency
                chunk_overlap=50,  # Overlap to preserve context at boundaries
                length_function=len,
                separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
            )
            
            def fixed_chunker(markdown_text: str):
                return self.text_splitter.create_documents([markdown_text])
            
            self.chunker = fixed_chunker
            self._initialized = True 

    def ingest_document(self, text: str, namespace: str = None, source: str = "uploaded_file"):
        """Ingests a document text into the vector store for a specific namespace."""
        print(f"--- Ingesting Document for Namespace: {namespace} ---")
        self.vector_index_strategy.create_or_load_vector_index(
            text,
            chunker=self.chunker,
            namespace=namespace,
            source=source
        )
        print("--- Document Ingested Successfully ---")


    def query(self, query_text: str, namespace: str = None):
        """The main query method with hybrid search support."""
        print(f"\n=== VECTOR_STORE.QUERY CALLED ===")
        print(f"Query text: {query_text}")
        print(f"Namespace: {namespace}")
        
        # HuggingFaceEmbeddings from langchain exposes embed_query for single strings
        query_embedding = self.embeddings_model.embed_query(query_text)
        print(f"Embedding generated: length={len(query_embedding)}")
        print(f"Calling semantic_search on: {type(self.vector_index_strategy).__name__}")
        
        # Pass both embedding and raw text for hybrid search
        results = self.vector_index_strategy.semantic_search(
            embeded_query=query_embedding,
            namespace=namespace,
            query_text=query_text  # Enable hybrid search
        )
        
        print(f"Results from semantic_search: {results[:100] if results else 'EMPTY'}...")
        print(f"=== VECTOR_STORE.QUERY COMPLETE ===\n")
        return results
    def delete_document(self, source: str, namespace: str = None):
        """Deletes all documents matching the source UUID."""
        return self.vector_index_strategy.delete_by_source(source=source, namespace=namespace)
