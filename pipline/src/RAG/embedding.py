from chromadb.utils import embedding_functions
import os
import chromadb
import json

GLOBAL_EMBEDDING_ENGINE = embedding_functions.DefaultEmbeddingFunction()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_PATH = os.path.join(BASE_DIR, "../../vector_store") 

def chunk_embedding( collection_slug: str, chunks: dict, vector_path: str = VECTOR_PATH):
    """Embeds the chunks using chromadb's inbuilt embedding function and saves the vector in vector store"""

    if not chunks:
        print(f"Could not found Chunks")
        
        return
    
    if not os.path.exists(vector_path):
        print(f"Vector store path not found: {vector_path}")
        print("Creating the vector_store directory: \n")
        os.makedirs(vector_path, exist_ok=True)

    client = chromadb.PersistentClient(path=vector_path)
    
    # 4. Grab Chroma's default internal embedding function (all-MiniLM-L6-v2)
    default_ef = embedding_functions.DefaultEmbeddingFunction()

    collection = client.get_or_create_collection(
        name=collection_slug,
        embedding_function=default_ef,
        metadata={"hnsw:space": "cosine"} # Using cosine similarity for code matching
    )

    if collection.count() > 0:
        print(f"Collection already exists with {collection.count()} records. Skipping creation.")
        return collection
    

    # 6. Extract arrays for bulk insertion
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        ids.append(chunk["id"])
        
        # This is the actual string content2 that gets converted into numerical vector arrays
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

    return collection


def search_query(collection_slug, query_text: str, vector_path: str, top_k: int = 5):
    """
    TASK REQUIREMENT: Operates directly on the stored vector_store folder path.
    Does NOT depend on the 'collection' return token from the embedding function.
    """
    # Guard: Ensure the vector directory exists before trying to open it
    if not os.path.exists(vector_path):
        print(f"Search Error: Vector store directory '{vector_path}' does not exist.")
        return None

    # Connect to the physical storage bins on disk independently
    client = chromadb.PersistentClient(path=vector_path)
    
    try:
        collection = client.get_collection(
            name=collection_slug,
            embedding_function=GLOBAL_EMBEDDING_ENGINE
        )
    except Exception as e:
        print(f"Search Error: Could not find indexed collection on disk. Details: {e}")
        return None

    print(f"[Standalone Search] Querying database directly for: '{query_text}'")
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
    return results


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CHUNK_PATH = os.path.join(BASE_DIR, "../../chunks.json")
    VECTOR_PATH = os.path.join(BASE_DIR, "../../vector_store")    

    chunk_embedding(CHUNK_PATH, VECTOR_PATH)


    query_text = "How does the function 'foo' work in the codebase?"   

    search_results = search_query(query_text, VECTOR_PATH, top_k=5)

    if search_results and 'ids' in search_results and search_results['ids'][0]:
        print("\n" + "="*80)
        print(f" VECTOR STORE RETRIEVAL MATCHES FOR: '{query_text}'")
        print("="*80)

        # Unpack the parallel arrays safely using standard indexing positioning
        match_ids = search_results['ids'][0]
        match_docs = search_results['documents'][0]
        match_meta = search_results['metadatas'][0]
        match_dist = search_results['distances'][0]

        # Iterate through items side-by-side using zip
        for rank, (id_, doc, meta, distance) in enumerate(zip(match_ids, match_docs, match_meta, match_dist), 1):
            print(f"\n[RANK {rank}] MATCH ID: {id_}")
            print(f"  Filepath : {meta.get('filepath')}")
            print(f"  Component: {meta.get('type').upper()} | Class: {meta.get('parent_class')}")
            print(f"  Range    : Lines {meta.get('start_line')} to {meta.get('end_line')}")
            print(f"  Distance : {distance:.4f} (Cosine Closeness)")
            print(f"  " + "-"*40)
            
            # Print the implementation block indented for visual alignment
            print("  SOURCE IMPLEMENTATION EXTRACTION:")
            indented_source = "\n".join(f"    {line}" for line in doc.splitlines())
            print(indented_source)
            print("\n" + "_"*80)
    else:
        print("\nWarning: No structural matches returned from vector store.")




