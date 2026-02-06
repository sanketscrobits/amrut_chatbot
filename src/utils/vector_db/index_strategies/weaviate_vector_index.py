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
    
    def keyword_search(self, query_text: str, namespace: str = None, limit: int = 10):
        """
        Perform BM25 keyword search.
        
        Args:
            query_text: The raw query string
            namespace: Optional namespace to search within
            limit: Maximum number of results
            
        Returns:
            List of matching objects with scores
        """
        try:
            collection = self.__client.collections.get(self.__collection_name)
            
            # Build BM25 query with optional namespace filter
            if namespace:
                response = collection.query.bm25(
                    query=query_text,
                    limit=limit,
                    return_metadata=["score"],
                    filters=Filter.by_property("namespace").equal(namespace)
                )
            else:
                response = collection.query.bm25(
                    query=query_text,
                    limit=limit,
                    return_metadata=["score"]
                )
            
            return response.objects
        except Exception as e:
            print(f"Warning: BM25 search failed: {e}")
            return []
    
    def hybrid_rank_fusion(self, vector_results, keyword_results, k=60):
        """
        Combine vector and keyword search results using reciprocal rank fusion.
        
        Args:
            vector_results: Results from vector search with (object, score) tuples
            keyword_results: Results from BM25 search
            k: Constant for rank fusion (default 60)
            
        Returns:
            Combined and reranked results
        """
        scores = {}
        
        # Add vector search scores
        for rank, (obj, score) in enumerate(vector_results, 1):
            chunk_text = obj.properties.get("chunk_text", "")
            if chunk_text:
                scores[chunk_text] = scores.get(chunk_text, 0) + (1.0 / (k + rank))
        
        # Add keyword search scores  
        for rank, obj in enumerate(keyword_results, 1):
            chunk_text = obj.properties.get("chunk_text", "")
            if chunk_text:
                scores[chunk_text] = scores.get(chunk_text, 0) + (1.0 / (k + rank))
        
        # Sort by combined score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        # Returns list of (chunk_text, score) tuples
        return ranked
    
    def semantic_search(self, embeded_query: list[float], namespace: str = None, query_text: str = None) -> str:
        """
        Perform HYBRID search using both vector similarity and BM25 keyword matching.
        
        Args:
            embeded_query: The embedded query vector
            namespace: Optional namespace to search within
            query_text: Raw query text for keyword search (optional but recommended)
            
        Returns:
            The most relevant context string
        """
        print(f"\n=== WEAVIATE HYBRID SEARCH ===")
        print(f"Namespace: {namespace}")
        
        try:
            collection = self.__client.collections.get(self.__collection_name)
            
            # 1. Vector search
            if namespace:
                vector_response = collection.query.near_vector(
                    near_vector=embeded_query,
                    limit=20,
                    return_metadata=["distance"],
                    filters=Filter.by_property("namespace").equal(namespace)
                )
            else:
                vector_response = collection.query.near_vector(
                    near_vector=embeded_query,
                    limit=20,
                    return_metadata=["distance"]
                )
            
            print(f"Vector search: {len(vector_response.objects)} results")
            
            # Convert to (object, similarity) tuples
            vector_matches = []
            for obj in vector_response.objects:
                distance = obj.metadata.distance if obj.metadata.distance is not None else 1.0
                similarity = 1 - distance
                # Lower threshold to 0.35 for better retrieval accuracy
                if similarity >= 0.35:
                    vector_matches.append((obj, similarity))
            
            print(f"Vector matches (>= 0.35): {len(vector_matches)}")
            
            # 2. Keyword search (if query_text provided)
            keyword_results = []
            if query_text:
                keyword_results = self.keyword_search(query_text, namespace, limit=10)
                print(f"Keyword search: {len(keyword_results)} results")
            
            # 3. Hybrid rank fusion
            if keyword_results:
                ranked = self.hybrid_rank_fusion(vector_matches, keyword_results)
                print(f"Combined results: {len(ranked)} unique chunks")
                
                if ranked:
                    # OPTIMIZATION: Return top 5 results concatenated to solve "Keyhole Problem"
                    top_k = 5
                    top_results = ranked[:top_k]
                    
                    params = []
                    for i, (chunk_text, score) in enumerate(top_results):
                        params.append(f"--- Context Chunk {i+1} (Score: {score:.4f}) ---\n{chunk_text}")
                    
                    combined_context = "\n\n".join(params)
                    
                    print(f"Best hybrid score: {ranked[0][1]:.4f}")
                    print(f"Returning {len(top_results)} chunks (approx {len(combined_context)} chars)")
                    print(f"=== END HYBRID SEARCH ===\n")
                    return combined_context
            else:
                # Fallback to vector-only
                print("Keyword search unavailable, using vector-only")
                if vector_matches:
                    vector_matches.sort(key=lambda x: x[1], reverse=True)
                    
                    # OPTIMIZATION: Return top 5 results concatenated
                    top_k = 5
                    top_results = vector_matches[:top_k]
                    
                    params = []
                    for i, (obj, score) in enumerate(top_results):
                        chunk_text = obj.properties.get("chunk_text", "")
                        params.append(f"--- Context Chunk {i+1} (Score: {score:.4f}) ---\n{chunk_text}")
                    
                    combined_context = "\n\n".join(params)

                    print(f"Best vector score: {vector_matches[0][1]:.4f}")
                    print(f"Returning {len(top_results)} chunks (approx {len(combined_context)} chars)")
                    print(f"=== END HYBRID SEARCH ===\n")
                    return combined_context or "No relevant context found for the question."
            
            print(f"No matches found")
            print(f"=== END HYBRID SEARCH ===\n")
            return "No relevant context found for the question."
            
        except Exception as e:
            print(f"Error during hybrid search: {e}")
            import traceback
            traceback.print_exc()
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
