import os
from streaming_assistants import patch
from openai import OpenAI
from swe_bench_util.index.file_util import EXCLUDE_EXTS

OPENAI_CLIENT = None


def open_ai_client():
    global OPENAI_CLIENT
    if OPENAI_CLIENT is None:
        OPENAI_CLIENT = patch(OpenAI())
    return OPENAI_CLIENT


def upload_file(file_path) -> str | None:
    """
    Index a file to Astra Assistants unless it is an excluded file type.
    If the upload is successful, it returns the file ID.
    If excluded or an error occurs, it prints an error message and returns None.
    """
    print(f"Processing {file_path}")
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
    # handle 501 for unsupported file types or other errors
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def index_to_astra_assistants(repo_dir):
    """
    This function indexes the files in the given repository directory.
    It walks through the directory, processes each file, and uploads it to the AI client.
    The file IDs are then returned as a list.
    """
    file_ids = []
    for root, dirs, files in os.walk(repo_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_id = upload_file(file_path)
            if file_id:
                file_ids.append(file_id)
    return file_ids
