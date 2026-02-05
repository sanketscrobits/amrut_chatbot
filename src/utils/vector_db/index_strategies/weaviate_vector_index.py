from src.utils.vector_db.index_strategies.base import VectorIndexStrategy
from settings import WEAVIATE_URL, WEAVIATE_API_KEY, WEAVIATE_COLLECTION_NAME
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter
import uuid


class WeaviateClientSingleton:
    """Singleton wrapper for Weaviate client connection with connection pooling."""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WeaviateClientSingleton, cls).__new__(cls)
        return cls._instance
    
    def get_client(self, url: str = WEAVIATE_URL, api_key: str = WEAVIATE_API_KEY):
        """Get or create Weaviate client instance."""
        if self._client is None:
            try:
                if api_key:
                    # For cloud or authenticated instances
                    auth_config = weaviate.auth.AuthApiKey(api_key=api_key)
                    self._client = weaviate.connect_to_custom(
                        http_host=url.replace("http://", "").replace("https://", ""),
                        http_port=80 if "http://" in url else 443,
                        http_secure=("https://" in url),
                        grpc_host=url.replace("http://", "").replace("https://", ""),
                        grpc_port=50051,
                        grpc_secure=("https://" in url),
                        auth_credentials=auth_config
                    )
                else:
                    # For local instances without authentication
                    host = url.replace("http://", "").replace("https://", "")
                    port_split = host.split(":")
                    if len(port_split) == 2:
                        host = port_split[0]
                        port = int(port_split[1])
                    else:
                        port = 8080
                    
                    self._client = weaviate.connect_to_local(
                        host=host,
                        port=port
                    )
                print(f"Connected to Weaviate at {url}")
            except Exception as e:
                print(f"Error connecting to Weaviate: {e}")
                raise e
        return self._client
    
    def close(self):
        """Close the Weaviate client connection."""
        if self._client is not None:
            self._client.close()
            self._client = None


class WeaviateVectorIndex(VectorIndexStrategy):
    """Weaviate implementation of VectorIndexStrategy."""
    
    def __init__(self, embeddings):
        self.__collection_name = WEAVIATE_COLLECTION_NAME
        self.__embeddings = embeddings
        self.__client_singleton = WeaviateClientSingleton()
        self.__client = self.__client_singleton.get_client()
        self.__collection = False
        self.__ensure_collection_exists()
    
    def __ensure_collection_exists(self):
        """Create collection schema if it doesn't exist."""
        try:
            # Check if collection exists
            if self.__client.collections.exists(self.__collection_name):
                print(f"Collection '{self.__collection_name}' already exists")
                self.__collection = True
                return
            
            # Create collection with schema
            self.__client.collections.create(
                name=self.__collection_name,
                vectorizer_config=Configure.Vectorizer.none(),  # We provide our own embeddings
                properties=[
                    Property(
                        name="chunk_text",
                        data_type=DataType.TEXT,
                        description="The text content of the chunk"
                    ),
                    Property(
                        name="chunk_id",
                        data_type=DataType.INT,
                        description="The sequential ID of the chunk"
                    ),
                    Property(
                        name="source",
                        data_type=DataType.TEXT,
                        description="Identifier for the source document"
                    ),
                    Property(
                        name="namespace",
                        data_type=DataType.TEXT,
                        description="Namespace for multi-tenancy"
                    )
                ]
            )
            print(f"Created collection '{self.__collection_name}'")
            self.__collection = True
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            raise e
    
    def create_or_load_vector_index(self, markdown_text: str, chunker=None, namespace: str = None, source: str = "uploaded_file"):
        """
        Create or load a vector index from markdown text.
        
        Args:
            markdown_text: The markdown text to index
            chunker: Optional callable to chunk the text
            namespace: Optional namespace for multi-tenancy
            source: Identifier for the source document
        """
        # Get the collection
        collection = self.__client.collections.get(self.__collection_name)
        
        # Use provided chunker callable if supplied
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
        
        # Embed documents using the embeddings model
        vectors = self.__embeddings.embed_documents(chunk_texts)
        
        # Prepare objects for batch insertion
        id_prefix = f"{source}_" if source else ""
        
        # Insert vectors with batch
        with collection.batch.dynamic() as batch:
            for i, (vector, chunk_text) in enumerate(zip(vectors, chunk_texts)):
                # Generate unique ID
                object_id = f"{id_prefix}chunk_{i}"
                
                # Create properties
                properties = {
                    "chunk_text": chunk_text,
                    "chunk_id": i,
                    "source": source,
                    "namespace": namespace if namespace else ""
                }
                
                # Add to batch
                batch.add_object(
                    properties=properties,
                    vector=vector,
                    uuid=uuid.uuid5(uuid.NAMESPACE_DNS, object_id)
                )
        
        # Log success
        if namespace:
            print(f"Uploaded {len(chunk_texts)} chunks to Weaviate collection '{self.__collection_name}' (Namespace: {namespace})")
        else:
            print(f"Uploaded {len(chunk_texts)} chunks to Weaviate collection '{self.__collection_name}' (Default Namespace)")
        
        self.__collection = True
        return self
    
    def semantic_search(self, embeded_query: list[float], namespace: str = None) -> str:
        """
        Perform semantic search using an embedded query.
        
        Args:
            embeded_query: The embedded query vector
            namespace: Optional namespace to search within
            
        Returns:
            The most relevant context string
        """
        try:
            collection = self.__client.collections.get(self.__collection_name)
            
            # Build query with optional namespace filter
            if namespace:
                response = collection.query.near_vector(
                    near_vector=embeded_query,
                    limit=20,
                    return_metadata=["distance"],
                    filters=Filter.by_property("namespace").equal(namespace)
                )
            else:
                response = collection.query.near_vector(
                    near_vector=embeded_query,
                    limit=20,
                    return_metadata=["distance"]
                )
            
            print(f"\n=== WEAVIATE SEARCH: {len(response.objects)} results returned ===")
            
            if response.objects:
                # Convert distance to similarity score (Weaviate uses distance metrics)
                # For cosine distance: similarity = 1 - distance
                # Filter results with score >= 0.7 (distance <= 0.3)
                matches = []
                all_scores = []
                for i, obj in enumerate(response.objects):
                    distance = obj.metadata.distance if obj.metadata.distance is not None else 1.0
                    similarity = 1 - distance
                    all_scores.append(similarity)
                    if i < 3:
                        print(f"  Result {i+1}: score={similarity:.4f}")
                    if similarity >= 0.5:  # Lowered from 0.7 to allow more matches
                        matches.append((obj, similarity))
                
                print(f"Matches above 0.5: {len(matches)}/{len(response.objects)}")
                if all_scores:
                    print(f"Best score: {max(all_scores):.4f}")
                print(f"=== END WEAVIATE SEARCH ===\n")
                
                if matches:
                    # Sort by similarity (highest first) and return top result
                    matches.sort(key=lambda x: x[1], reverse=True)
                    context = matches[0][0].properties.get("chunk_text", "")
                    return context or "No relevant context found for the question."
                return "No relevant context found for the question (low score)."
            else:
                return "No relevant context found for the question."
        except Exception as e:
            print(f"Error during semantic search: {e}")
            return "Error retrieving context."
    
    def delete_by_source(self, source: str, namespace: str = None):
        """
        Delete all vectors matching the source metadata field.
        
        Args:
            source: The source identifier to delete
            namespace: Optional namespace to delete from
        """
        try:
            collection = self.__client.collections.get(self.__collection_name)
            
            # Build filter for deletion
            if namespace:
                # Delete by both source and namespace
                filter_condition = (
                    Filter.by_property("source").equal(source) &
                    Filter.by_property("namespace").equal(namespace)
                )
            else:
                # Delete by source only
                filter_condition = Filter.by_property("source").equal(source)
            
            # Delete matching objects
            result = collection.data.delete_many(
                where=filter_condition
            )
            
            print(f"Deleted {result.successful} documents with source '{source}' from namespace '{namespace}'")
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            raise e


# Default Setup for easy import
from langchain_huggingface import HuggingFaceEmbeddings

try:
    _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = WeaviateVectorIndex(embeddings=_embeddings)
except Exception as e:
    print(f"Warning: Could not initialize default Weaviate index: {e}")
    vector_store = None
