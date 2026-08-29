"""Answer checking. Deterministic, and generous about form.

A child who writes "19 Rest 7", "19 R 7" or "19 R7" has done the same correct
division three ways. Marking any of them wrong is a bug with a real cost, so
normalisation is deliberately permissive about notation and strict only about
the number.
"""

import re
import unicodedata
from dataclasses import dataclass

from .models import Task

# German writes thousands with . or a space, decimals with a comma, and the
# remainder as "R", "r" or "Rest".
_REMAINDER_RE = re.compile(r"\s*(?:r(?:est)?)\s*", re.I)
_THOUSANDS_RE = re.compile(r"(?<=\d)[.   ](?=\d{3}\b)")


def normalise(value: str) -> str:
    """Canonical form of a written answer. Empty string when it holds no number."""
    text = unicodedata.normalize("NFKC", value).strip().lower()
    text = text.replace("=", " ").strip()
    text = _THOUSANDS_RE.sub("", text)
    text = _REMAINDER_RE.sub(" r ", text)
    text = text.replace(",", ".")
    text = re.sub(r"\s+", " ", text).strip()

    parts = re.findall(r"-?\d+(?:\.\d+)?", text)
    if not parts:
        return ""

    if " r " in f" {text} " and len(parts) >= 2:
        return f"{_trim(parts[0])} R {_trim(parts[1])}"
    return _trim(parts[0])


def _trim(number: str) -> str:
    if "." in number:
        number = number.rstrip("0").rstrip(".")
    return number or "0"


def is_correct(given: str, expected: str) -> bool:
    left, right = normalise(given), normalise(expected)
    if not left:
        return False
    if left == right:
        return True
    # "42 R 0" and "42" are the same answer.
    return left.replace(" R 0", "") == right.replace(" R 0", "")


@dataclass
class BlankResult:
    blank_id: str
    label: str
    given: str
    correct: bool


@dataclass
class TaskResult:
    task_id: str
    results: list[BlankResult]

    @property
    def all_correct(self) -> bool:
        return all(r.correct for r in self.results)

    @property
    def wrong(self) -> list[BlankResult]:
        return [r for r in self.results if not r.correct]


def grade(task: Task, answers: dict[str, str]) -> TaskResult:
    """Check one task. Unanswered blanks count as not yet correct, never as wrong."""
    results = []
    for blank in task.blanks:
        given = (answers.get(blank.id) or "").strip()
        results.append(
            BlankResult(
                blank_id=blank.id,
                label=blank.label,
                given=given,
                correct=bool(given) and is_correct(given, blank.answer),
            )
        )
    return TaskResult(task_id=task.id, results=results)
