#!/bin/bash
set -euo pipefail

# Available ENV vars include:

# BENCH_TEST_PATCH
# BENCH_VERSION
# BENCH_FAIL_TO_PASS
# BENCH_INSTANCE_ID
# BENCH_BASE_COMMIT
# BENCH_REPO
# BENCH_PROBLEM_STATEMENT
# BENCH_PASS_TO_PASS

# BENCH_REPO_DIR
# CALLING_CWD

echo "# Problem statement"
echo "$BENCH_PROBLEM_STATEMENT"

# Recommend files
echo "# Random .py files in the git working tree"

FILE_HINT=$(cd $BENCH_REPO_DIR && git ls-files '*.py' | shuf -n 30)

JSON_STRING=$( jq -n \
                  --arg id "$BENCH_INSTANCE_ID" \
                  --arg file_hint "$FILE_HINT" \
                  '{id: $id, file_hint: ($file_hint | split("\r?\n"; ""))}' )

echo $JSON_STRING >> "examples/file_hints.jsonl"