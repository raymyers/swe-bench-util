"""This module provides the CLI."""
from dataclasses import asdict
from typing import Optional
import json
import sys
import os
import subprocess
import typer
from datasets import load_dataset
from dotenv import load_dotenv

from swe_bench_util import __app_name__, __version__
from swe_bench_util.file_hint_eval import eval_file_hints_vs_oracle, BenchExample, FileHint

from swe_bench_util.index.astra_assistants import (
    index_to_astra_assistants,
    create_assistant,
    get_retrieval_file_ids,
)

app = typer.Typer()
get_app = typer.Typer()
app.add_typer(get_app, name="get")
index_app = typer.Typer()
app.add_typer(index_app, name="index")

load_dotenv("./.env")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


def write_file(path, text):
    with open(path, "w") as f:
        f.write(text)
        print(f"File '{path}' was saved", file=sys.stderr)


def write_json(path, name, data):
    json_str = json.dumps(data, indent=2)
    json_path = f"{path}/{name}.json"
    try:
        write_file(json_path, json_str)
    except Exception as e:
        raise e


def format_markdown_code_block(text):
    text = text.replace("```", "\\`\\`\\`")
    return f"```\n{text}\n```"


def write_markdown(path, name, data):
    template_fields = ["instance_id" "repo", "base_commit", "problem_statement"]
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
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
        print(f"Directory '{repo_dir}' was created.")
    if not os.path.exists(f"{repo_dir}/.git"):
        # Clone the repo if the directory doesn't exist
        result = subprocess.run(
            ["git", "clone", repo_url, repo_dir],
            check=True,
            text=True,
            capture_output=True,
        )
        print("Output:", result.stdout)
        print("Error:", result.stderr)


def checkout_commit(repo_dir, commit_hash):
    subprocess.run(["git", "checkout", commit_hash], cwd=repo_dir, check=True)


def checkout_dir(dataset_name: str, repo: str):
    return f"checkouts/{dataset_name}/{repo.replace('/', '__')}"


def checkout_repo_at_commit(repo: str, dataset_name: str, base_commit: str) -> str:
    repo_url = f"git@github.com:{repo}.git"
    path = checkout_dir(dataset_name, repo)
    maybe_clone(repo_url, path)
    # Worktrees are another option here if we want to support concurrent checkouts
    checkout_commit(path, base_commit)
    return path


@app.command()
def checkout(
    split: str = "dev",
    dataset_name="princeton-nlp/SWE-bench",
    repo: Optional[str] = None,
    id: Optional[str] = None,
    exec: Optional[str] = None,
):
    dataset = load_filtered_dataset(split, dataset_name, repo=repo, id=id)
    for row_data in dataset:
        path = checkout_repo_at_commit(
            row_data["repo"], dataset_name, row_data["base_commit"]
        )
        print(f"checked out to '{path}'")
        if exec:
            env_vars = {
                **os.environ,
                **{
                    f"BENCH_{key.upper()}": str(value)
                    for key, value in row_data.items()
                },
            }
            env_vars["CALLING_CWD"] = os.getcwd()
            env_vars["BENCH_REPO_DIR"] = path
            # This will raise if the command is unsuccessful.
            result = subprocess.run(exec, check=True, env=env_vars, shell=True)
            print(f"Command: '{exec}', Exit Code: {result.returncode}")


@index_app.command()
def astra_assistants(
    split: str = "dev",
    dataset_name="princeton-nlp/SWE-bench",
    max: int = 1,
    repo: Optional[str] = None,
    id: Optional[str] = None,
):
    dataset = load_filtered_dataset(split, dataset_name, repo=repo, id=id)
    if len(dataset) > max:
        user_input = input(
            f"Selected {len(dataset)} entries in split {split}. Do you want to continue indexing? (y/n): "
        )
        if user_input.lower() != "y":
            print("Aborting.")
            return
    bench_list = []
    file_list = []
    search_string_list = []
    for row_data in dataset:
        id = row_data["instance_id"]
        path = checkout_repo_at_commit(
            row_data["repo"], dataset_name, row_data["base_commit"]
        )
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory '{path}' was created.")
        file_id_path_mapping = []
        if os.path.exists(f"{path}/{id}-file_ids.json"):
            with open(f"{path}/{id}-file_ids.json", "r") as file:
                print(f"trying to load file {file} from {path}/{id}-file_ids.json")
                file_id_path_mapping = json.load(file)
        else:
            file_id_path_mapping, excluded_files = index_to_astra_assistants(path)
            write_file(f"{path}/{id}-file_ids.json", json.dumps(file_id_path_mapping, indent=2))
            write_file(
                f"{path}/{id}-excluded_files.json", json.dumps(excluded_files, indent=2)
            )
        assistant_id = ""
        if os.path.exists(f"{path}/{id}-assistant_id.txt"):
            with open(f"{path}/{id}-assistant_id.txt", "r") as file:
                print(f"trying to load file {file} from {path}/{id}-assistant_id.txt")
                assistant_id = file.read()
        else:
            file_ids = list(file_id_path_mapping.keys())

            assistant = create_assistant(file_ids, id)
            write_file(f"{path}/{id}-assistant_id.txt", assistant.id)
            assistant_id = assistant.id
        retrieval_file_ids, search_strings = get_retrieval_file_ids(assistant_id, row_data)
        search_string_list.append(search_strings[0])
        file_names = []
        for retrieval_file_id in retrieval_file_ids:
            file_names.append(file_id_path_mapping[retrieval_file_id])
        file_list += [FileHint(id = id, hint_files = file_names)]
        repo = row_data["repo"]
        bench_list += oracle(split=split, dataset_name=dataset_name, repo=repo, id=id)
    evals = eval_file_hints_vs_oracle(bench_list, file_list)
    i = 0
    dict_evals = []
    for eval in evals:
        eval.search_string=search_string_list[i]
        dict_evals.append(asdict(eval))
        i+=1
    print(eval)
    write_json("recall","results", dict_evals)


@get_app.command()
def rows(
    split: str = "dev",
    dataset_name: str = "princeton-nlp/SWE-bench",
    repo: Optional[str] = None,
    id: Optional[str] = None,
):
    """Download one example"""
    dataset = load_filtered_dataset(split, dataset_name, repo=repo, id=id)
    for row_data in dataset:
        row_id = row_data["instance_id"]
        write_json("examples", f"{row_id}", row_data)
        write_markdown("examples", f"{row_id}", row_data)


def load_filtered_dataset(
    split: str, dataset_name: str, repo: Optional[str] = None, id: Optional[str] = None
):
    print(f"using --dataset-name '{dataset_name}' --split '{split}'")
    dataset = load_dataset(dataset_name, split=split)
    if repo:
        print(f"      --repo '{repo}'")
        dataset = dataset.filter(lambda el: el["repo"] == repo)
    if id:
        print(f"      --id '{id}'")
        dataset = dataset.filter(lambda el: el["instance_id"] == id)
    return dataset


def diff_file_names(text: str) -> list[str]:
    return [
        line[len("+++ b/") :] for line in text.split("\n") if line.startswith("+++")
    ]


@get_app.command()
def oracle(
    split: str = "dev",
    dataset_name="princeton-nlp/SWE-bench",
    repo: Optional[str] = None,
    id: Optional[str] = None,
):
    """Download oracle (patched files) for all examples in split"""
    dataset = load_filtered_dataset(split, dataset_name, repo=repo, id=id)
    result = []
    for row_data in dataset:
        patch_files = diff_file_names(row_data["patch"])
        test_patch_files = diff_file_names(row_data["test_patch"])
        result.append(
            BenchExample(
                id = row_data["instance_id"],
                repo = row_data["repo"],
                base_commit = row_data["base_commit"],
                patch_files = patch_files,
                test_patch_files = test_patch_files,
            )
        )
    dict_result = [asdict(row) for row in result]
    write_json("examples", "oracle", dict_result)
    return result


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    return
