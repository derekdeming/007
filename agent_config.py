import os
from dotenv import load_dotenv

load_dotenv()  

# OpenAI stuff
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))

# GitHub stuff 
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "")
MAX_FILE_CHUNK_SIZE = int(os.getenv("MAX_FILE_CHUNK_SIZE", "12000"))
LOCAL_CLONE_PATH = os.getenv("LOCAL_CLONE_PATH", "../cloned_repo_agent")

# A prefix for generated commit messages to differentiate them
COMMIT_PREFIX = "[Autonomous Agent]"
