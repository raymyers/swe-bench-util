"""
A file hint means, "What files should we modify for this request"
For metric explanation:
https://en.wikipedia.org/wiki/Precision_and_recall
"""

from dataclasses import dataclass


@dataclass
class BenchExample:
    id: str
    repo: str
    base_commit: str
    patch_files: list[str]
    test_patch_files: list[str]


@dataclass
class FileHint:
    """Recommendation of files to edit for the problem statement"""

    id: str
    hint_files: list[str]


@dataclass
class FileHintAssessed:
    id: str
    hint_files: list[str]
    patch_files: list[str]
    test_patch_files: list[str]
    precision: float
    recall: float


def eval_file_hints_vs_oracle(
    examples: list[BenchExample], hints: list[FileHint]
) -> list[FileHintAssessed]:
    """
    For every recommendation that is present in examples patch, calculate precision and recall.
    Files in test_patch that are recommended are ignored.
    """
    hint_evals = []
    for hint in hints:
        for example in examples:
            if hint.id == example.id:
                # Ignore test patch files
                hint_files = set(hint.hint_files) - set(example.test_patch_files)
                precision = calc_precision(example, hint_files)
                recall = calc_recall(example, hint_files)
                hint_evals.append(
                    FileHintAssessed(
                        id=hint.id,
                        hint_files=hint.hint_files,
                        patch_files=example.patch_files,
                        test_patch_files=example.test_patch_files,
                        precision=precision,
                        recall=recall,
                    )
                )
    return hint_evals


def calc_precision(example: BenchExample, hint_files: set[str]) -> float:
    true_positives = hint_files & set(example.patch_files)
    if len(hint_files) == 0:
        return 0.0 if len(example.patch_files) > 0 else 1.0
    return len(true_positives) / len(hint_files)


def calc_recall(example: BenchExample, hint_files: set[str]) -> float:
    true_positives = hint_files & set(example.patch_files)
    if len(example.patch_files) == 0:
        return 1.0
    return len(true_positives) / len(example.patch_files)
