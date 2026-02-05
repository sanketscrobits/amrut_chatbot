import sys
from pathlib import Path

# Add project root to sys path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.vector_db.loader_strategies.local_loader import LocalLoader
from src.utils.vector_db.vector_store_factory import create_vector_store
from src.utils.vector_db.vector_store_singleton import VectorStoreSingleton
from settings import NAMESPACE

class MyDocumentUploader:
    def __init__(self):
        """Initialize the uploader with necessary strategies."""
        self.embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.document_loader_strategy = LocalLoader()
        # Use factory pattern to create vector store based on VECTOR_DB_TYPE setting
        self.vector_index_strategy = create_vector_store(embeddings=self.embeddings_model)
        
        self.vector_store = VectorStoreSingleton(
            embeddings_model=self.embeddings_model,
            document_loader_strategy=self.document_loader_strategy,
            vector_index_strategy=self.vector_index_strategy,
        )

    def upload_document(self, file_path: str, uuid: str, namespace: str = None):
        """
        Uploads a single document to Pinecone.
        
        Args:
            file_path: Absolute path to the file to upload.
            uuid: Unique identifier for the document source.
            namespace: Pinecone namespace. Uses settings.NAMESPACE if None.
        """
        target_namespace = namespace or NAMESPACE
        if not target_namespace:
            raise ValueError("Namespace not specified and not found in settings.")

        print(f"Processing file: {file_path} for UUID: {uuid}")
        
        # Load content using Docling (via LocalLoader)
        markdown_content = self.document_loader_strategy.load_documents(path=file_path)
        
        if not markdown_content:
            print(f"Warning: No content extracted from {file_path}")
            return False

        # Ingest into vector store
        self.vector_store.ingest_document(
            text=markdown_content,
            namespace=target_namespace,
            source=uuid
        )
        return True

if __name__ == "__main__":
    # Example usage for testing
    import argparse
    parser = argparse.ArgumentParser(description="Upload document to Pinecone.")
    parser.add_argument("file_path", help="Path to file")
    parser.add_argument("uuid", help="UUID for the source")
    args = parser.parse_args()
    
    uploader = MyDocumentUploader()
    uploader.upload_document(args.file_path, args.uuid)
