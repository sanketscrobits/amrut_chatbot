from src.utils.vector_db.loader_strategies.base import DocumentLoaderStrategy
from src.utils.vector_db.index_strategies.base import VectorIndexStrategy
from langchain_experimental.text_splitter import SemanticChunker
path = r"F:\ScroBits_Tech\Query-Agent\documents\MIREMS.pdf"

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
            self.text_splitter = SemanticChunker(embeddings_model, breakpoint_threshold_type="percentile")
            def semantic_chunker(markdown_text: str):
                return self.text_splitter.create_documents([markdown_text])
            self.chunker = semantic_chunker
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
        # HuggingFaceEmbeddings from langchain exposes embed_query for single strings
        query_embedding = self.embeddings_model.embed_query(query_text)
        """The main query method."""
        # We don't need to auto-build vectorstore anymore as we rely on uploaded data
        results = self.vector_index_strategy.semantic_search(embeded_query=query_embedding, namespace=namespace)
        return results
    def delete_document(self, source: str, namespace: str = None):
        """Deletes all documents matching the source UUID."""
        return self.vector_index_strategy.delete_by_source(source=source, namespace=namespace)
