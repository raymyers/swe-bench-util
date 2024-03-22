# SWE-bench Util
Scripts for working with SWE-bench, the AI coding agent benchmark.

If you are trying to beat Devin, see also The [SWE-bench fork](https://github.com/OpenAgentsInc/SWE-bench) from OpenAgentsInc to run your agent.

## Features
* See usage info with `--help` and `<subcommand> --help`
  * `python -m swe_bench_util --help`
* `get rows` Download SWE-bench examples from HuggingFace to json file
* `get oracle` Get "oracle" patch file lists parsed from diffs ([context](https://github.com/raymyers/swe-bench-util/issues/1))
* `checkout` Clone the repo for an example and checkout the base_commit
* `index astra_assistants` checkout example then upload to DataStack's [Astra Assistants](https://www.datastax.com/blog/introducing-the-astra-assistants-api) using phact's [streaming-assistants](https://github.com/phact/streaming-assistants) library

## Setup

Install poetry if you don't have it
```sh
python3 -m pip install poetry
```

If using a feature that requires a vendor API, copy `.env.example` to `.env` and fill in the values.

Install dependencies and initialize an editable command
```sh
poetry install
```

## Run

```sh
swe_bench_util --help
```

This assumes the poetry install has gone onto your path, otherwise you can use `python -m swe_bench_util`.


Save the first example case. This will download the full dataset on first run, caching it with the `datasets` library.

```sh
swe_bench_util get rows --split 'dev[0:1]'
```


Output
```
File 'examples/sqlfluff__sqlfluff-4764.json' was saved
File 'examples/sqlfluff__sqlfluff-4764.md' was saved
```

Use jq to show a subset of the JSON.

```sh
jq '. | {repo, instance_id, base_commit, problem_statement}' examples/sqlfluff__sqlfluff-4764.json
```

Save the Oracle (patched file list) for the dev subset.
```sh
swe_bench_util get oracle
```
Output:
```
File 'examples/oracle.json' was saved
```
```sh
jq '.[] | .repo' examples/oracle.json  | jq -s 'unique'
jq '.[] | {repo, base_commit}' examples/oracle.json  | jq -s 'unique'
```
Git checkout the repo / base_commit of an example.
`swe-bench-util checkout --id pydicom__pydicom-793`


index and run inference with astra-assistants:

Make sure you have your keys set up in `.env`

```sh
cp .env.backup .env
```

and set your keys. Then run the index command:


```sh
swe_bench_util index astra-assistants
```

Output:

```
...
Files used in retrieval: ["test_wcs.py", "wcs.py", "test_utils.py", "test_transform_coord_meta.py", "CHANGES.rst", "test_images.py", "test_misc.py"]
...
```


## Data

By default, most commands will operate on the `dev` split, using the Huggingface [datasets](https://huggingface.co/docs/datasets/loading) API. You can specify a split using `--split`, for instance:

* `--split dev` the entire dev split
* `--split 'dev[0:10]'` first 10 rows
* `--split 'dev[:10%]'` 10% sample

You can also filter by repo or id. Filters are applied *after* split, so if you select a row range and a filter you may come up empty.
* `--repo pydicom/pydicom`
* `--id pydicom__pydicom-1555`

Here is the shape of the data.

```
    dev: Dataset({
        features: ['repo', 'instance_id', 'base_commit', 'patch', 'test_patch', 'problem_statement', 'hints_text', 'created_at', 'version', 'FAIL_TO_PASS', 'PASS_TO_PASS', 'environment_setup_commit'],
        num_rows: 225
    })
    test: Dataset({
        features: ['repo', 'instance_id', 'base_commit', 'patch', 'test_patch', 'problem_statement', 'hints_text', 'created_at', 'version', 'FAIL_TO_PASS', 'PASS_TO_PASS', 'environment_setup_commit'],
        num_rows: 2294
    })
    train: Dataset({
        features: ['repo', 'instance_id', 'base_commit', 'patch', 'test_patch', 'problem_statement', 'hints_text', 'created_at', 'version', 'FAIL_TO_PASS', 'PASS_TO_PASS', 'environment_setup_commit'],
        num_rows: 19008
    })
```

## Checks

```sh
make check
```

That is equivelant to:

```sh
python -m pytest

python -m ruff check --fix

python -m ruff format
```
