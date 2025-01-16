import os
import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from agent_config import LOCAL_CLONE_PATH, COMMIT_PREFIX
from github_utils import (
    clone_or_pull_repo,
    get_all_files,
    multi_commit_push
)
from openai_utils import (
    summarize_and_suggest,
    generate_code_modifications,
    parse_changes
)

def run_advanced_agent(github_repo_url: str):
    print(f"\n{'='*40}\n[START] Advanced Agent Run @ {datetime.datetime.now()}")
    repo = clone_or_pull_repo(github_repo_url)
    if not repo:
        print("[ERROR] Could not clone/pull repo. Exiting.")
        return

    # 1) Gather local file contents
    all_file_paths = get_all_files()
    repo_files_dict = {}
    for fpath in all_file_paths:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                repo_files_dict[fpath] = f.read()
        except:
            # Binary or unreadable files are skipped
            pass

    # 2) Summarize & get suggestions
    summary, suggestions = summarize_and_suggest(repo_files_dict)
    print("\n[SUMMARY OF REPO]\n", summary[:500], "...")  # truncated print
    print("\n[SUGGESTIONS]\n", suggestions)

    # 3) Generate code modifications
    structured_answer = generate_code_modifications(summary, suggestions)
    modifications = parse_changes(structured_answer)

    if not modifications:
        print("[INFO] No modifications returned by AI. Agent run ends.")
        return

    print(f"[INFO] The AI proposed changes to {len(modifications)} files.")
    changed_files = []
    for filename, new_content in modifications.items():
        target_path = os.path.join(LOCAL_CLONE_PATH, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            with open(target_path, "w", encoding="utf-8") as wf:
                wf.write(new_content)
            changed_files.append(target_path)
        except Exception as e:
            print(f"[ERROR] Writing to {target_path} failed: {e}")

    if changed_files:
        print(f"[INFO] Attempting multiple commits for {len(changed_files)} changed file(s).")
        base_msg = "AI-driven code improvements"
        multi_commit_push(changed_files, base_msg, commits_count=3)
        # Increase commits_count if you want more commits (like 100/day).

    print("[DONE] Agent run complete.\n")


def main():
    run_advanced_agent("https://github.com/derekdeming/graphs.git")

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=run_advanced_agent,
        trigger='interval',
        days=1,
        kwargs={"github_repo_url": "https://github.com/derekdeming/graphs.git"},
        id="daily-run",
        replace_existing=True
    )

    scheduler.start()
    print("[INFO] Scheduler started. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("[INFO] Scheduler stopped.")


if __name__ == "__main__":
    main()
