# SWE-bench Util
Scripts for working with SWE-bench, the AI coding agent benchmark.

If you are trying to beat Devin, see also The [SWE-bench fork](https://github.com/OpenAgentsInc/SWE-bench) from OpenAgentsInc to run your agent.

## Features
* See usage info with `--help` and `<subcommand> --help`
  * `python -m swe_bench_util --help`
* `get row` Download SWE-bench examples from HuggingFace to json file
* `get oracle` Get "oracle" patch file lists parsed from diffs ([context](https://github.com/raymyers/swe-bench-util/issues/1))
* `checkout` Clone the repo for an example and checkout the base_commit
* `index astra_assistants` checkout example then upload to DataStack's [Astra Assistants](https://www.datastax.com/blog/introducing-the-astra-assistants-api) using phact's [streaming-assistants](https://github.com/phact/streaming-assistants) library

## Setup

Setup venv
```sh
python3 -m venv ./venv
source venv/bin/activate
```

If using a feature that requires a vendor API, copy `.env.example` to `.env` and fill in the values.

Install dependencies
```sh
python -m pip install -r requirements.txt
```

## Run
```sh
python -m swe_bench_util --help
```

Save the first example case. This will download the full dataset on first run, caching it with the `datasets` library.

```sh
python -m swe_bench_util get row
```


Output
```
File 'rows/sqlfluff__sqlfluff-4764.json' was saved
File 'rows/sqlfluff__sqlfluff-4764.md' was saved
```

Use jq to show a subset of the JSON.

```sh
jq '. | {repo, instance_id, base_commit, problem_statement}' rows/sqlfluff__sqlfluff-4764.json
```

Save the Oracle (patched file list) for the dev subset.
```sh
python -m swe_bench_util get oracle
```
Output:
```
File 'rows/oracle.json' was saved
```
```sh
jq '.[] | .repo' rows/oracle.json  | jq -s 'unique'
jq '.[] | {repo, base_commit}' rows/oracle.json  | jq -s 'unique'
```

## Data

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
