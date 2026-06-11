import git
from pathlib import Path

local_repo_path = Path(__file__).parent.parent / "notebook"

def cloning_repo(repo_url: str, local_path: str) -> git.Repo:
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

cloning_repo("https://github.com/flypythoncom/python.git",local_repo_path)