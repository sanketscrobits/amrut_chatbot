# Vector Database Examples

This directory contains example scripts demonstrating how to use the vector database implementations in the AMRUT Chatbot project.

## Available Implementations

The project supports two vector database implementations:

1. **Pinecone** - Cloud-hosted vector database
2. **Weaviate** - Self-hosted vector database

Both implementations follow the `VectorIndexStrategy` interface, allowing seamless switching between them.

## Example Files

### 1. `vector_db_pinecone_example.py`

Demonstrates using Pinecone vector database with the VectorStoreSingleton.

**Run:**
```bash
python examples/vector_db_pinecone_example.py
```

**Requirements:**
- Pinecone API key configured in `.env`
- `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` set

---

### 2. `vector_db_weaviate_example.py`

Demonstrates using Weaviate vector database with the VectorStoreSingleton.

**Setup Weaviate (Docker):**
```bash
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  --name weaviate \
  semitechnologies/weaviate:latest
```

**Run:**
```bash
python examples/vector_db_weaviate_example.py
```

**Requirements:**
- Weaviate running locally or remotely
- `WEAVIATE_URL` configured (default: `http://localhost:8080`)

---

### 3. `vector_db_switching.py`

Demonstrates three methods to switch between vector database implementations:

1. **Environment Variables** - Set `VECTOR_DB_TYPE=weaviate` or `VECTOR_DB_TYPE=pinecone`
2. **Direct Instantiation** - Explicitly create `PineconeVectorIndex` or `WeaviateVectorIndex`
3. **Factory Pattern** (Recommended) - Use `create_vector_store(embeddings, db_type="weaviate")`

**Run:**
```bash
python examples/vector_db_switching.py
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Pinecone Configuration
PINECONE_API_KEY=your_api_key_here
PINECONE_INDEX_NAME=your_index_name
PINECONE_REGION=your_region
PINECONE_HOST=your_host

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=optional_api_key_for_cloud
WEAVIATE_COLLECTION_NAME=AmrutChatbotDocs

# Vector Database Selection
VECTOR_DB_TYPE=pinecone  # or "weaviate"
```

## Switching Between Implementations

### Method 1: Environment Variable (Recommended for Production)

```bash
export VECTOR_DB_TYPE=weaviate
```

```python
from src.utils.vector_db.vector_store_factory import create_vector_store

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = create_vector_store(embeddings)  # Reads from environment
```

### Method 2: Factory with Explicit Type

```python
from src.utils.vector_db.vector_store_factory import create_vector_store

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Use Weaviate
vector_store = create_vector_store(embeddings, db_type="weaviate")

# Or use Pinecone
vector_store = create_vector_store(embeddings, db_type="pinecone")
```

### Method 3: Direct Instantiation

```python
from src.utils.vector_db.index_strategies.weaviate_vector_index import WeaviateVectorIndex

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = WeaviateVectorIndex(embeddings=embeddings)
```

## Common Operations

### Ingest Documents

```python
vector_store.create_or_load_vector_index(
    markdown_text="Your document text here",
    namespace="user_123",
    source="doc_uuid_456"
)
```

### Semantic Search

```python
query_embedding = embeddings.embed_query("What are the features?")
result = vector_store.semantic_search(query_embedding, namespace="user_123")
print(result)
```

### Delete Documents

```python
vector_store.delete_by_source(source="doc_uuid_456", namespace="user_123")
```

## Adding New Vector Database Implementations

To add a new vector database (e.g., ChromaDB, Qdrant):

1. Create a new file: `src/utils/vector_db/index_strategies/your_db_vector_index.py`
2. Implement the `VectorIndexStrategy` interface
3. Add the implementation to `vector_store_factory.py`
4. Update this README

## Dependencies

Install required packages:

```bash
# For Pinecone
pip install pinecone-client

# For Weaviate
pip install weaviate-client==4.9.3

# Common dependencies
pip install langchain-huggingface
pip install sentence-transformers
```
