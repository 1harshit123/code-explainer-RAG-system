from chromadb.utils import embedding_functions
import os
import chromadb
import json


def chunk_embedding(chunk_path: str, vector_path: str):
    """Embeds the chunks using chromadb's inbuilt embedding function and saves the vector in vector store"""

    if not os.path.exists(chunk_path):
        print(f"Chunk file not found: {chunk_path}")
        return
    
    if not os.path.exists(vector_path):
        print(f"Vector store path not found: {vector_path}")
        return
    
    with open(chunk_path, "r", encoding="utf-8") as f:
        chunk_data = json.load(f)
    
    client = chromadb.PersistentClient(path=vector_path)
    
    # 4. Grab Chroma's default internal embedding function (all-MiniLM-L6-v2)
    default_ef = embedding_functions.DefaultEmbeddingFunction()

    # 5. Create or get your vector collection database table
    collection = client.get_or_create_collection(
        name="codebase_rag_collection",
        embedding_function=default_ef,
        metadata={"hnsw:space": "cosine"} # Using cosine similarity for code matching
    )

    # 6. Extract arrays for bulk insertion
    ids = []
    documents = []
    metadatas = []

    for chunk in chunk_data:
        ids.append(chunk["id"])
        
        # This is the actual string content that gets converted into numerical vector arrays
        documents.append(chunk["embed_text"])
        
        # Flatten lists into simple comma-separated strings so Chroma can index the metadata
        metadata_entry = {
            "name": chunk["name"],
            "type": chunk["type"],
            "parent_class": chunk["parent_class"] if chunk["parent_class"] else "None",
            "filepath": chunk["filepath"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"]
        }
        metadatas.append(metadata_entry)

    # 7. Bulk update/insert everything into your local database folder
    print(f"Generating embeddings and indexing data inside local store at: {vector_path}...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"Success! Database populated. Total indexed vector records: {collection.count()}")


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CHUNK_PATH = os.path.join(BASE_DIR, "../../chunks.json")
    VECTOR_PATH = os.path.join(BASE_DIR, "../../vector_store")    

    chunk_embedding(CHUNK_PATH, VECTOR_PATH)    




