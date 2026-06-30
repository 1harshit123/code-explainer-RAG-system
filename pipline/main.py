from pipline.src.repoAbstraction import cloning_repo, chunking
from pipline.src.RAG.embedding import chunk_embedding
from pipline.src.RAG.retrival import analyze_codebase_query
import git


def processing_repo(repoLink: str, collection_slug: str) -> bool:
    if not repoLink or not repoLink.strip():
        print("[RAG Pipeline] Aborted: Received empty repository string.")
        return False
    # Cloning the repo
    try:
        repoObject = cloning_repo(repoLink)
        if not isinstance(repoObject, git.Repo):
            print("[RAG Pipeline] Step 1 Failed: Object returned is not a valid git.Repo instance.")
            return False
            
    except Exception as e:
        print(f"[RAG Pipeline] Step 1 Failed: Error during cloning execution -> {e}")
        return False
    
    # Chunking
    try:
        chunking()
        
    except Exception as e:
        print(f"[RAG Pipeline] Step 2 Failed: Error during chunking execution -> {e}")
        return False

    # Execute Embedding Generation
    try:
        chunk_embedding(collection_slug)
        
    except Exception as e:
        print(f"[RAG Pipeline] Step 3 Failed: Error during embedding generation -> {e}")
        return False

    print("[RAG Pipeline] Success: End-to-end repository ingestion complete.")
    return True

    




        

    

    
    

