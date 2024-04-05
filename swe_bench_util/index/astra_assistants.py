import json
import os
import concurrent.futures
import threading
from functools import partial

from tqdm import tqdm
from streaming_assistants import patch
from openai import OpenAI
from openai.lib.streaming import AssistantEventHandler
from typing_extensions import override
from swe_bench_util.index.file_util import EXCLUDE_EXTS, exponential_backoff_retry

OPENAI_CLIENT = None

open_ai_client_lock = threading.Lock()


def open_ai_client():
    global OPENAI_CLIENT
    with open_ai_client_lock:  # Acquire the lock before checking OPENAI_CLIENT
        if OPENAI_CLIENT is None:
            OPENAI_CLIENT = patch(OpenAI())
    return OPENAI_CLIENT


def upload_file(file_path) -> str | None:
    """
    Index a file to Astra Assistants unless it is an excluded file type.
    If the upload is successful, it returns the file ID.
    If excluded or an error occurs, it prints an error message and returns None.
    """
    try:
        if any(file_path.endswith(ext) for ext in EXCLUDE_EXTS):
            print(f"Skipping {file_path} because it has an excluded extension")
            return None
        file = open_ai_client().files.create(
            file=open(
                file_path,
                "rb",
            ),
            purpose="assistants",
            embedding_model="text-embedding-3-large",
        )
        return file.id
    except Exception as e:
        raise e


file_ids_lock = threading.Lock()
excluded_files_lock = threading.Lock()

def index_to_astra_assistants(repo_dir):
    """
    Indexes files in the repository directory, uploads them, and returns their IDs.
    """
    # Generate a list of file paths to upload
    file_paths = [
        os.path.join(root, file)
        for root, _, files in os.walk(repo_dir)
        for file in files
    ]
    total_files = len(file_paths)

    print("going to upload {total_files} files")
    # Initialize the progress bar
    pbar = tqdm(total=total_files, desc="Uploading files")

    file_ids = {}
    excluded_files = []

    # Define a wrapper function to use with each file upload
    def upload_and_progress(file_path, repo_dir):
        try:
            file_id = exponential_backoff_retry(upload_file, file_path)
            if file_id is not None:
                with file_ids_lock:  # Ensure thread-safe append operation
                    file_ids[file_id] = file_path[len(repo_dir)+1:]
            else:
                with excluded_files_lock:  # Ensure thread-safe append operation
                    excluded_files.append(file_path)
        finally:
            # Update the progress bar in a thread-safe manner
            pbar.update(1)

    upload_with_repo = partial(upload_and_progress, repo_dir=repo_dir)
    # Use ThreadPoolExecutor to upload files in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map each file upload task to the executor
        executor.map(upload_with_repo, file_paths)

    # Ensure the progress bar is closed upon completion
    pbar.close()

    print(f"All uploaded file IDs: {file_ids}")
    return file_ids, excluded_files


system_prompt = """
    You are a developer, you will be provided with a partial code base and a github issue description explaining a programming problem to resolve.
    Solve the issue by generating a single patch file that can be applied directly to this repository using git apply. Please respond with a single patch file in the following format (no yapping).
    <patch>
    --- a/file.py
    +++ b/file.py
    @@ -1,27 +1,35 @@
    def euclidean(a, b):
    -    while b:
    -        a, b = b, a % b
    -    return a
    +    if b == 0:
    +        return a
    +    return euclidean(b, a % b)


    def bresenham(x0, y0, x1, y1):
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    -    sx = 1 if x0 < x1 else -1
    -    sy = 1 if y0 < y1 else -1
    -    err = dx - dy
    +    x, y = x0, y0
    +    sx = -1 if x0 > x1 else 1
    +    sy = -1 if y0 > y1 else 1

    -    while True:
    -        points.append((x0, y0))
    -        if x0 == x1 and y0 == y1:
    -            break
    -        e2 = 2 * err
    -        if e2 > -dy:
    +    if dx > dy:
    +        err = dx / 2.0
    +        while x != x1:
    +            points.append((x, y))
    err -= dy
    -            x0 += sx
    -        if e2 < dx:
    -            err += dx
    -            y0 += sy
    +            if err < 0:
    +                y += sy
    +                err += dx
    +            x += sx
    +    else:
    +        err = dy / 2.0
    +        while y != y1:
    +            points.append((x, y))
    +            err -= dx
    +            if err < 0:
    +                x += sx
    +                err += dy
    +            y += sy

    +    points.append((x, y))
    return points
    </patch>
    """

def create_assistant(file_ids, id):
    client = open_ai_client()
    #assistant = client.beta.assistants.retrieve(id)
    #if assistant is not None:
    #    return assistant
    #else:
    # create assistant
    assistant = client.beta.assistants.create(
        file_ids=file_ids,
        model="gpt-4-0125-preview",
        instructions=system_prompt,
        name=id,
        tools=[{"type": "retrieval"}],
    )
    return assistant


class EventHandler(AssistantEventHandler):
    # init
    def __init__(self):
        super().__init__()
        self.file_ids = []
        self.search_strings = []

    @override
    def on_run_step_done(self, run_step) -> None:
        chunks = [
            chunk.retrieval
            for chunk in run_step.step_details.tool_calls
            if chunk.retrieval
        ][0]
        self.file_ids = list(set([chunk["file_id"] for chunk in chunks]))
        self.search_strings = list(set([chunk["search_string"] for chunk in chunks]))
        print(f"Files used in retrieval: {json.dumps(self.file_ids)}")


def get_retrieval_file_ids(assistant_id, row_data):
    client = open_ai_client()

    user_prompt = f"""
    <issue>
    {row_data["problem_statement"]}
    </issue>
    """
    print("creating persistent thread and message")
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_prompt
    )
    print(f"running inference for {row_data['instance_id']}")

    handler = EventHandler()
    print("creating run")
    with open_ai_client().beta.threads.runs.create_and_stream(
        thread_id=thread.id,
        assistant_id=assistant_id,
        event_handler=handler,
    ) as stream:
        # stream.until_done()
        print("producing diff:")
        for text in stream.text_deltas:
            print(text, end="", flush=True)
            print()
        return handler.file_ids, handler.search_strings
