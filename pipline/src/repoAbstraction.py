import git
from pathlib import Path
import json

from pipline.src.chuking import process_repo

local_repo_path = Path(__file__).parent.parent / "notebook"

def cloning_repo(repo_url: str, local_path: str = local_repo_path) -> git.Repo:
    try:
        print("Attempting to clone using 'master' branch...")
        return git.Repo.clone_from(repo_url, local_path, branch="master")
        
    except git.exc.GitCommandError as e:
        if "Remote branch master not found" in str(e) or "did not match any file" in str(e):
            print("'master' branch not found. Retrying with 'main' branch...")
            try:
                return git.Repo.clone_from(repo_url, local_path, branch="main")
            except Exception as retry_error:
                print(f"Failed to clone with 'main' branch as well: {retry_error}")
                raise
        else:
            print(f"Git error encountered (not branch related): {e}")
            raise
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def chunking():
    import sys
    import shutil
    repo_path = local_repo_path

    print(f"Processing repo: {repo_path}")
    chunks = process_repo(repo_path)
    print(f"Extracted {len(chunks)} chunks")

    out_path = "chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Saved to {out_path}")

    try:
        print(f"Cleaning up: Deleting {repo_path} folder...")
        shutil.rmtree(repo_path)
        print("Folder successfully deleted.")
    except Exception as e:
        print(f"Warning: Could not delete folder {repo_path}: {e}")



    # quick preview
    if chunks:
        print("\n── Sample chunk (embed_text field) ──")
        print(chunks[0]["embed_text"][:600])

chunking()
