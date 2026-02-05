# AMRUT Chatbot - Weaviate Dependency

## Installation

To use Weaviate vector database, install the weaviate-client:

```bash
pip install weaviate-client==4.9.3
```

## Optional: Add to requirements.txt (if it exists)

```txt
weaviate-client==4.9.3
```

## Weaviate Setup

### Option 1: Docker (Recommended for local development)

```bash
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  --name weaviate \
  semitechnologies/weaviate:latest
```

### Option 2: Weaviate Cloud Services (WCS)

Sign up at https://console.weaviate.cloud/ and use the provided URL and API key.

## Configuration

Add to your `.env` file:

```bash
# Vector Database Selection
VECTOR_DB_TYPE=weaviate  # or "pinecone"

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=  # Optional, only for cloud instances
WEAVIATE_COLLECTION_NAME=AmrutChatbotDocs
```

## Verification

Test the installation:

```python
import weaviate

# For local instance
client = weaviate.connect_to_local()
print(client.is_ready())
client.close()
```
