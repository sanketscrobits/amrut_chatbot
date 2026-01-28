from src.utils.vector_db.index_strategies.pinecone_vector_index import chunking_and_embedding
from src.utils.vector_db.index_strategies.pinecone_vector_index import vector_index_strategies


embeddings, chunks = chunking_and_embedding().embedding()
index = vector_index_strategies().index
index_name = vector_index_strategies().index_name

pinecone_vectors = []
for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
    vector_data = {
        "id": f"chunk_{i}",
        "values": embedding.tolist(),
        "metadata": {
            "chunk_text": chunk.page_content,
            "chunk_id": i,
            "source": "documents_folder"
        }
    }
    pinecone_vectors.append(vector_data)

index.upsert(vectors=pinecone_vectors)
print(f"Uploaded {len(pinecone_vectors)} chunks to Pinecone index '{index_name}'")
