import git
from pathlib import Path
import json

from pipline.src.chuking import process_repo

THIS_FILE_ABS_PATH = Path(__file__).resolve()


PIPELINE_ABS_DIR = THIS_FILE_ABS_PATH.parent.parent

local_repo_path = Path(__file__).parent.parent / "notebook"

import shutil



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
    print(f"Processing repo: {local_repo_path}")
    chunks = process_repo(local_repo_path) # returning in the last
    print(f"Extracted {len(chunks)} chunks")


    try:
        print(f"Cleaning up: Deleting {local_repo_path} folder...")
        shutil.rmtree(local_repo_path)
        print("Folder successfully deleted.")
    except Exception as e:
        print(f"Warning: Could not delete folder {local_repo_path}: {e}")

    if chunks:
        print("\n── Sample chunk (embed_text field) ──")
        print(chunks[0]["embed_text"][:600])

    return chunks

    


