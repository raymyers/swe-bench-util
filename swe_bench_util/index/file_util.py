import random
import time

EXCLUDE_EXTS: list[str] = [
    ".min.js",
    ".min.js.map",
    ".min.css",
    ".min.css.map",
    ".tfstate",
    ".tfstate.backup",
    ".jar",
    ".ipynb",
    ".idx",
    ".pack",
    ".png",
    ".odg",
    ".bz2",
    ".xz",
    ".fits",
    ".jpg",
    ".jpeg",
    ".download",
    ".gif",
    ".bmp",
    ".tiff",
    ".ico",
    ".mp3",
    ".wav",
    ".wma",
    ".ogg",
    ".flac",
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".patch",
    ".patch.disabled",
    ".wmv",
    ".m4a",
    ".m4v",
    ".3gp",
    ".3g2",
    ".rm",
    ".swf",
    ".flv",
    ".iso",
    ".bin",
    ".tar",
    ".zip",
    ".7z",
    ".gz",
    ".rar",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".svg",
    ".parquet",
    ".pyc",
    ".pub",
    ".pem",
    ".ttf",
    ".dfn",
    ".dfm",
    ".feature",
    "pnpm-lock.yaml",
    "LICENSE",
    "poetry.lock",
]

def exponential_backoff_retry(upload_func, file_path, max_retries=1000, initial_wait=1.0, backoff_factor=2, max_wait=60):
    """
    Wraps the upload function to implement exponential backoff in case of rate limiting,
    with a maximum wait time.

    :param upload_func: The function to execute that may need retries.
    :param file_path: The path to the file being uploaded.
    :param max_retries: Maximum number of retries.
    :param initial_wait: Initial wait time in seconds before the first retry.
    :param backoff_factor: Factor by which the wait time increases after each retry.
    :param max_wait: Maximum wait time in seconds between retries.
    """
    retries = 0
    wait_time = initial_wait

    while retries < max_retries:
        try:
            return upload_func(file_path)
        except Exception as e:
            if e.status_code == 429:  # Rate limited
                print(f"Rate limited, retrying {file_path} after {wait_time} seconds...")
                time.sleep(wait_time)
                retries += 1
                wait_time = min(wait_time * backoff_factor, max_wait)  # Increase wait time but cap at max_wait
                # Optional: add jitter to avoid the thundering herd problem
                wait_time += random.uniform(0, wait_time * 0.1)
            else:
                print(f"Error processing {file_path}: {e}")
                return None
    print(f"Maximum retries exceeded for {file_path}")
    return None
