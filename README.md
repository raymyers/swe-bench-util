# SWE-bench Util
Scripts for working with SWE-bench, the AI coding agent benchmark 

## Setup

Setup venv
```
python3 -m venv ./venv
source venv/bin/activate
```

Install dependencies
```
python -m pip install -r requirements.txt
```

## Run
```
python -m swe_bench_util --help
```

Save the first example case. This will download the full dataset on first run, caching it with the `datasets` library.

```
python -m swe_bench_util get
```

Output
```
File 'rows/sqlfluff__sqlfluff-4764.json' was saved
File 'rows/sqlfluff__sqlfluff-4764.md' was saved
```

Use jq to show a subset of the JSON.

```
jq '. | {repo, instance_id, base_commit, problem_statement}' rows/sqlfluff__sqlfluff-4764.json
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
