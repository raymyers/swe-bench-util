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
python -m swe_bench_util
```

Show the first example case:

```
python -m swe_bench_util get
```

Use jq to show a subset of the JSON.

```
python -m swe_bench_util get | jq '. | {repo, instance_id, base_commit, problem_statement, , FAIL_TO_PASS, PASS_TO_PASS}'
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
