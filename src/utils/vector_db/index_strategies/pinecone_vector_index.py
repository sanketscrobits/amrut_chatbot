from src.utils.vector_db.index_strategies.base import VectorIndexStrategy
from settings import PINECONE_API_KEY, PINECONE_INDEX_NAME
from pinecone import Pinecone

class PineconeVectorIndex(VectorIndexStrategy):
    def  __init__ (self, embeddings):
        self.__collection_name = PINECONE_INDEX_NAME
        self.__api_key = Pinecone(api_key=PINECONE_API_KEY)
        self.__embeddings = embeddings
        self.__collection = False

    def create_or_load_vector_index(self, markdown_text: str, chunker=None, namespace: str = None, source: str = "uploaded_file"):
        # We process ingestion regardless of self.__collection state because in API upload mode
        # we might call this multiple times for different files.
        # However, reusing the client is fine.
        
        index = self.__api_key.Index(self.__collection_name)
        # Use provided chunker callable if supplied; it may return Documents or strings
        if chunker is not None:
            chunk_outputs = chunker(markdown_text)
            if chunk_outputs and hasattr(chunk_outputs[0], "page_content"):
                chunk_texts = [c.page_content for c in chunk_outputs]
            else:
                chunk_texts = list(chunk_outputs)
        else:
            # Fallback: no chunker provided; treat whole markdown as a single chunk
            chunk_texts = [markdown_text] if markdown_text else []
        if not chunk_texts:
            self.__collection = True
            return self

        # Embed documents using langchain's HuggingFaceEmbeddings
        vectors = self.__embeddings.embed_documents(chunk_texts)
        pinecone_vectors = []
        
        # Use UUID (source) in ID prefix to ensure uniqueness if needed, or stick to simple chunk_i collision risk?
        # The original code used f"chunk_{i}". If we upload multiple files, they will overwrite each other
        # if using the same ID logic in the same namespace.
        # Better to prefix with source if available.
        id_prefix = f"{source}_" if source else ""
        
        for i, (values, chunk_text) in enumerate(zip(vectors, chunk_texts)):
            pinecone_vectors.append({
                "id": f"{id_prefix}chunk_{i}",
                "values": values,
                "metadata": {
                    "chunk_text": chunk_text,
                    "chunk_id": i,
                    "source": source
                }
            })

        # Upsert to Pinecone
        # Pass namespace if provided
        if namespace:
             index.upsert(vectors=pinecone_vectors, namespace=namespace)
             print(f"Uploaded {len(pinecone_vectors)} chunks to Pinecone index '{self.__collection_name}' (Namespace: {namespace})")
        else:
             index.upsert(vectors=pinecone_vectors)
             print(f"Uploaded {len(pinecone_vectors)} chunks to Pinecone index '{self.__collection_name}' (Default Namespace)")
             
        self.__collection = True
        return self
    
    def semantic_search(self, embeded_query: list[float], namespace: str = None) -> str:
        index = self.__api_key.Index(self.__collection_name)
        
        query_params = {
            "vector": embeded_query,
            "top_k": 20,
            "include_metadata": True,
            # "score_threshold": 0.7 
        }
        if namespace:
            query_params["namespace"] = namespace
            
        try:
            response = index.query(**query_params)
            
            if response.get("matches"):
                # Filter by score manually if needed since threshold param availability depends on client/setup
                matches = [m for m in response["matches"] if m.get('score', 0) >= 0.7]
                if matches:
                    # Combine contexts potentially? Or just return top 1
                    context = matches[0]["metadata"].get("chunk_text", "")
                    return context or "No relevant context found for the question."
                return "No relevant context found for the question (low score)."
            else:
                return "No relevant context found for the question."
        except Exception as e:
            print(f"Error during semantic search: {e}")
            return "Error retrieving context."
    def delete_by_source(self, source: str, namespace: str = None):
        """Delete all vectors matching the source metadata field."""
        index = self.__api_key.Index(self.__collection_name)
        
        try:
            # Delete by metadata filter
            # Filter structure: {"source": {"$eq": source}}
            delete_params = {
                "filter": {"source": {"$eq": source}}
            }
            if namespace:
                delete_params["namespace"] = namespace
            
            index.delete(**delete_params)
            print(f"Deleted documents with source '{source}' from namespace '{namespace}'")
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            raise e

from langchain_huggingface import HuggingFaceEmbeddings

# Default Setup for easy import
try:
    _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = PineconeVectorIndex(embeddings=_embeddings)
except Exception as e:
    print(f"Warning: Could not initialize default Pinecone index: {e}")
    vector_store = None
