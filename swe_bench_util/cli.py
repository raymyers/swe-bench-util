"""This module provides the CLI."""

from typing import Optional
import json
import sys
import os
import subprocess
import typer
from swe_bench_util import __app_name__, __version__
from datasets import load_dataset
from dotenv import load_dotenv
from openai import OpenAI

from streaming_assistants import patch


app = typer.Typer()
get_app = typer.Typer()
app.add_typer(get_app, name="get")

load_dotenv("./.env")

OPENAI_CLIENT = None
def open_ai_client():
    global OPENAI_CLIENT
    if OPENAI_CLIENT is None:
        OPENAI_CLIENT = patch(OpenAI())
    return OPENAI_CLIENT

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


def write_file(path, text):
    with open(path, 'w') as f:
        f.write(text)
        print(f"File '{path}' was saved", file=sys.stderr)

def write_json(path, name, data):
    json_str = json.dumps(data, indent=2)
    json_path = f"{path}/{name}.json"
    write_file(json_path, json_str)

def format_markdown_code_block(text):
    text = text.replace('```', '\\`\\`\\`')
    return f"```\n{text}\n```"

def write_markdown(path, name, data):
    template_fields = [
        "instance_id"
        "repo",
        "base_commit",
        "problem_statement"
    ]
    text = f"""# {data['instance_id']}

* repo: {data['repo']}
* base_commit: {data['base_commit']}

## problem_statement
{data['problem_statement']}
"""
    for k, v in data.items():
        if k not in template_fields:
            text += f"""## {k}\n{format_markdown_code_block(v)}\n\n"""
    md_path = f"{path}/{name}.md"
    write_file(md_path, text)

def maybe_clone(repo_url, repo_dir):
    if not os.path.exists(f"{repo_dir}/.git"):
        # Clone the repo if the directory doesn't exist
        result = subprocess.run(['git', 'clone', repo_url, repo_dir], check=True, text=True, capture_output=True)
        print("Output:", result.stdout)
        print("Error:", result.stderr)

def checkout_commit(repo_dir, commit_hash):
    subprocess.run(['git', 'checkout', commit_hash], cwd=repo_dir, check=True)

exclude_exts: list[str] = [
    ".min.js",
    ".min.js.map",
    ".min.css",
    ".min.css.map",
    ".tfstate",
    ".tfstate.backup",
    ".jar",
    ".ipynb",
    ".png",
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
    "sweep.yaml",
    "pnpm-lock.yaml",
    "LICENSE",
    "poetry.lock",
]
def upload_file(file_path):
    # Your processing logic for each file
    print(f"Processing {file_path}")
    try:
        if any(file_path.endswith(ext) for ext in exclude_exts):
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

def process_files_in_repo(repo_dir):
    file_ids = []
    for root, dirs, files in os.walk(repo_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_id = upload_file(file_path)
            if file_id:
                file_ids.append(file_id)
    return file_ids

@app.command()
def get(index:int=0, split: str='dev', dataset_name='princeton-nlp/SWE-bench'):
    dataset = load_dataset(dataset_name, split=split)
    row_data = dataset[index]
    id = row_data['instance_id']
    path = f'{dataset_name}-{split}'
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' was created.")
    write_json(path, f"{id}", row_data)
    write_markdown(path, f"{id}", row_data)

@app.command()
def process_repo_files(index:int=0, split: str='dev', dataset_name='princeton-nlp/SWE-bench'):
    dataset = load_dataset(dataset_name, split=split)
    row_data = dataset[index]
    repo_name = row_data['repo'].split('/')[-1]
    repo = f'git@github.com:{row_data["repo"]}.git'
    base_commit = row_data['base_commit']
    path = f'/tmp/{dataset_name}-{split}/{repo_name}/{base_commit}'
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' was created.")
    maybe_clone(repo, path)
    checkout_commit(path, base_commit)
    file_ids = process_files_in_repo(path)
    path = f'{dataset_name}-{split}'
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' was created.")
    write_file(f"{path}/file_ids.json", json.dumps(file_ids, indent=2))

@get_app.command()
def row(index:int=0, split: str='dev', dataset_name='princeton-nlp/SWE-bench'):
    """Download one row"""
    dataset = load_dataset(dataset_name, split=split)
    row_data = dataset[index]
    id = row_data['instance_id']
    write_json('rows', f"{id}", row_data)
    write_markdown('rows', f"{id}", row_data)
    
def diff_file_names(text: str) -> list[str]:
    return [
        line[len("+++ b/"):] 
        for line in text.split('\n') 
        if line.startswith('+++')
    ]

@get_app.command()
def oracle(split: str='dev', dataset_name='princeton-nlp/SWE-bench'):
    """Down load oracle (patched files) for all rows in split"""
    dataset = load_dataset(dataset_name, split=split)
    result = []
    for row_data in dataset:
        patch_files = diff_file_names(row_data['patch'])
        test_patch_files = diff_file_names(row_data['test_patch'])
        result.append({
            "id": row_data['instance_id'],
            "repo": row_data['repo'],
            "base_commit": row_data['base_commit'],
            "patch_files": patch_files,
            "test_patch_files": test_patch_files 
        })
    write_json('rows', "oracle", result)

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return
