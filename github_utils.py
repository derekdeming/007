import os
from git import Repo, exc
from agent_config import LOCAL_CLONE_PATH, COMMIT_PREFIX
import datetime

def clone_or_pull_repo(github_repo_url: str) -> Repo:
    """
    Clones or pulls a remote repo using the local user's Git credentials.
    If the repo is not cloned locally, it will clone it.
    If it's already cloned, it will just do a `git pull`.
    """
    try:
        if not os.path.exists(LOCAL_CLONE_PATH):
            print(f"Cloning {github_repo_url} into {LOCAL_CLONE_PATH} using local credentials...")
            # Just pass the URL; GitPython will use local user credentials
            Repo.clone_from(github_repo_url, LOCAL_CLONE_PATH)
        else:
            print("Attempting to pull using local credentials.")
            repo = Repo(LOCAL_CLONE_PATH)
            repo.remotes.origin.pull()
        return Repo(LOCAL_CLONE_PATH)
    except exc.GitCommandError as e:
        print(f"[ERROR] Git operation failed: {e}")
        return None


def get_all_files():
    """
    Returns a list of all file paths in the local repository (excluding .git).
    """
    repo_files = []
    for root, dirs, files in os.walk(LOCAL_CLONE_PATH):
        if ".git" in root:
            continue
        for file in files:
            repo_files.append(os.path.join(root, file))
    return repo_files


def stage_commit_and_push(file_paths, commit_message):
    """
    Stages the specified file paths, creates a commit, and pushes using local credentials.
    """
    try:
        repo = Repo(LOCAL_CLONE_PATH)
        repo.index.add(file_paths)
        repo.index.commit(commit_message)
        repo.remotes.origin.push()
        print(f"[SUCCESS] Pushed commit: {commit_message}")
        return True
    except Exception as e:
        print(f"[ERROR] Could not commit/push changes: {e}")
        return False


def multi_commit_push(file_paths, base_commit_msg, commits_count=5):
    """
    Example function to break changes into multiple smaller commits.
    If you have a large code diff, you can slice it up.
    This helps illustrate the idea of 'pushing 100 commits a day'.
    """
    try:
        repo = Repo(LOCAL_CLONE_PATH)

        # check if commits_count is valid
        if commits_count < 1:
            commits_count = 1

        chunk_size = max(len(file_paths) // commits_count, 1)
        start = 0
        commit_number = 1

        while start < len(file_paths):
            chunk = file_paths[start:start+chunk_size]
            commit_msg = f"{COMMIT_PREFIX} {base_commit_msg} (part {commit_number})"
            
            repo.index.add(chunk)
            repo.index.commit(commit_msg)
            print(f"  --> Committed chunk {commit_number} with {len(chunk)} file(s).")
            
            # Push each chunk separately
            repo.remotes.origin.push()
            print(f"  --> Pushed chunk {commit_number} successfully.")
            start += chunk_size
            commit_number += 1
        return True

    except Exception as e:
        print(f"[ERROR] multi_commit_push encountered an issue: {e}")
        return False
