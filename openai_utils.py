from time import sleep
import math
import random
import openai
from openai import OpenAI
# from openai.error import RateLimitError, APIConnectionError, APIError

from agent_config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    MAX_FILE_CHUNK_SIZE
)

client = OpenAI(api_key=OPENAI_API_KEY)

def call_with_retries(api_call_func, max_retries=5):
    """
    Makes an OpenAI API call with limited retries and exponential backoff
    to handle RateLimitError, APIConnectionError, or general APIError.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return api_call_func()
        except openai.RateLimitError as e:
            if attempt == max_retries:
                print(f"[ERROR] Reached max retries. Raising exception: {e}")
                raise
            else:
                # Exponential backoff + small jitter
                sleep_time = math.pow(2, attempt) + random.uniform(0, 1)
                print(f"[WARN] API error: {e}. Attempt {attempt}/{max_retries}. Retrying in {sleep_time:.1f}s...")
                sleep(sleep_time)


def chunk_text(text, max_chunk_size=12000):
    """
    Splits a large text into smaller chunks, each up to `max_chunk_size` characters.
    Avoids exceeding token limits. Real code might do more complex chunking (sentence-based, etc.).
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chunk_size, len(text))
        chunks.append(text[start:end])
        start += max_chunk_size
    return chunks


def summarize_and_suggest(repo_file_dict):
    """
    Summarize the entire codebase and suggest improvements.
    We’ll chunk large file contents and prompt the model in pieces.
    """
    master_summary = "Summary of the repository:\n"
    for file_path, content in repo_file_dict.items():
        # Chunk if too large
        file_chunks = chunk_text(content, MAX_FILE_CHUNK_SIZE)
        partial_summaries = []
        for chunk_idx, chunk in enumerate(file_chunks):
            prompt_text = (
                f"You are analyzing a repository file. Below is a chunk of file '{file_path}'.\n"
                f"Chunk {chunk_idx+1}:\n{chunk}\n\n"
                "Please provide a short summary of this chunk (no more than 50 words)."
            )

            # Use call_with_retries
            response = call_with_retries(lambda: client.chat.completions.create(
                model=OPENAI_MODEL,
                store=False,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=OPENAI_TEMPERATURE
            ))
            partial_summary = response.choices[0].message["content"]
            partial_summaries.append(partial_summary)

        # Combine partial summaries
        combined_summary = " ".join(partial_summaries)
        master_summary += f"\nFile: {file_path}\nSummary: {combined_summary}\n\n"

    # Finally, ask for improvement suggestions across the entire codebase
    improvement_prompt = (
        f"Based on the code summaries:\n{master_summary}\n\n"
        "Provide a list of potential improvements or new features (as bullet points)."
    )

    # Use call_with_retries
    improvement_resp = call_with_retries(lambda: client.chat.completions.create(
        model=OPENAI_MODEL,
        store=False,
        messages=[{"role": "user", "content": improvement_prompt}],
        temperature=OPENAI_TEMPERATURE
    ))
    suggestions = improvement_resp.choices[0].message["content"]

    return master_summary, suggestions


def generate_code_modifications(summary, suggestions):
    """
    Uses the summary and suggestions to propose actual code changes.
    The response is expected to describe which files to create/modify,
    with sample code. You can parse the response carefully.
    """
    prompt_text = (
        "You are an advanced code refactoring AI. Based on:\n"
        f"Summary:\n{summary}\n\n"
        f"Suggestions:\n{suggestions}\n\n"
        "Propose a series of code modifications that can be directly applied. "
        "Format your response as a structured list of changes:\n\n"
        "FILENAME: <new content>\n---\n"
        "FILENAME: <new content>\n---\n"
        "Only return the structured list. No extra commentary."
    )

    # Use call_with_retries
    response = call_with_retries(lambda: client.chat.completions.create(
        model=OPENAI_MODEL,
        store=False,
        messages=[{"role": "user", "content": prompt_text}],
        temperature=OPENAI_TEMPERATURE
    ))
    structured_answer = response.choices[0].message["content"]
    return structured_answer


def parse_changes(structured_answer):
    """
    Parses the AI's structured answer:
    FILENAME: <content>
    ---
    FILENAME: <content>
    ---
    into a dict {filename: new_content}
    """
    modifications = {}
    sections = structured_answer.split("---")
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if ":" in section:
            filename_part, content_part = section.split(":", 1)
            filename = filename_part.strip()
            new_content = content_part.strip()
            modifications[filename] = new_content
    return modifications
