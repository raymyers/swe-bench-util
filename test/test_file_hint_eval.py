from swe_bench_util.file_hint_eval import (
    eval_file_hints_vs_oracle,
    BenchExample,
    FileHint,
    calc_precision,
    calc_recall,
)

EXAMPLE_1 = {
    "id": "sqlfluff__sqlfluff-4764",
    "repo": "sqlfluff/sqlfluff",
    "base_commit": "a820c139ccbe6d1865d73c4a459945cd69899f8f",
    "patch_files": [
        "src/sqlfluff/cli/commands.py",
        "src/sqlfluff/cli/formatters.py",
        "src/sqlfluff/core/linter/linted_dir.py",
    ],
    "test_patch_files": ["test/cli/commands_test.py"],
}

EXAMPLE_1_NO_HINT = {
    "id": "sqlfluff__sqlfluff-4764",
    "hint_files": [],
}

EXAMPLE_1_ALL_HINT = {
    "id": "sqlfluff__sqlfluff-4764",
    "hint_files": [
        "src/sqlfluff/cli/commands.py",
        "src/sqlfluff/cli/formatters.py",
        "src/sqlfluff/core/linter/linted_dir.py",
    ],
}

EXAMPLE_1_ONE_TRUE_HINT = {
    "id": "sqlfluff__sqlfluff-4764",
    "hint_files": ["src/sqlfluff/core/linter/linted_dir.py"],
}

EXAMPLE_1_ALL_AND_TEST_HINT = {
    "id": "sqlfluff__sqlfluff-4764",
    "hint_files": [
        "src/sqlfluff/cli/commands.py",
        "src/sqlfluff/cli/formatters.py",
        "src/sqlfluff/core/linter/linted_dir.py",
        "test/cli/commands_test.py",
    ],
}

EXAMPLE_EMPTY = {
    "id": "sqlfluff__sqlfluff-empty",
    "repo": "sqlfluff/sqlfluff",
    "base_commit": "a820c139ccbe6d1865d73c4a459945cd69899f8f",
    "patch_files": [],
    "test_patch_files": [],
}


def test_batch_precision_and_recall_no_recommendations():
    examples = [BenchExample(**EXAMPLE_1)]
    recommendations = [FileHint(**EXAMPLE_1_NO_HINT)]
    results = eval_file_hints_vs_oracle(examples, recommendations)
    assert len(results) == 1
    assert results[0].precision == 0
    assert results[0].recall == 0


def test_batch_precision_and_recall_all_recommendations():
    examples = [BenchExample(**EXAMPLE_1)]
    recommendations = [FileHint(**EXAMPLE_1_ALL_HINT)]
    results = eval_file_hints_vs_oracle(examples, recommendations)
    assert len(results) == 1
    assert results[0].precision == 1
    assert results[0].recall == 1


def test_batch_precision_and_recall_one_true_recommendation():
    examples = [BenchExample(**EXAMPLE_1)]
    recommendations = [FileHint(**EXAMPLE_1_ONE_TRUE_HINT)]
    results = eval_file_hints_vs_oracle(examples, recommendations)
    assert len(results) == 1
    assert results[0].precision == 1
    assert results[0].recall == 1 / 3


def test_batch_precision_and_recall_all_and_test_recommendations():
    """
    Remove the test_patch files from the hint set
    """
    examples = [BenchExample(**EXAMPLE_1)]
    recommendations = [FileHint(**EXAMPLE_1_ALL_AND_TEST_HINT)]
    results = eval_file_hints_vs_oracle(examples, recommendations)
    assert len(results) == 1
    assert results[0].precision == 1
    assert results[0].recall == 1


def test_calc_precision_no_hint():
    """
    When there are no hints, precision is 0 unless target is also empty
    """
    assert calc_precision(BenchExample(**EXAMPLE_1), set([])) == 0
    assert calc_precision(BenchExample(**EXAMPLE_EMPTY), set([])) == 1


def test_calc_recall_empty_example():
    """
    When there are no patch_files, recall is 1
    """
    assert calc_recall(BenchExample(**EXAMPLE_EMPTY), set([])) == 1
