import pytest

from app.tutor.exercises.grading import grade, is_correct, normalise
from app.tutor.exercises.models import Blank, Task


@pytest.mark.parametrize(
    "written, expected",
    [
        # The same division, written the way different children write it.
        ("19 R 7", "19 R 7"),
        ("19R7", "19 R 7"),
        ("19 r 7", "19 R 7"),
        ("19 Rest 7", "19 R 7"),
        ("19 rest 7", "19 R 7"),
        ("= 19 R 7", "19 R 7"),
        # German number formatting.
        ("1.000", "1000"),
        ("1 000", "1000"),
        ("12,5", "12.5"),
        ("12,50", "12.5"),
        # Noise around the number.
        ("  615  ", "615"),
        ("615.", "615"),
        ("", ""),
        ("keine Ahnung", ""),
    ],
)
def test_normalisation_accepts_how_children_actually_write(written, expected):
    assert normalise(written) == expected


@pytest.mark.parametrize(
    "given, expected",
    [
        ("19 Rest 7", "19 R 7"),
        ("19R7", "19 R 7"),
        ("1.000", "1000"),
        ("1 000", "1000"),
        ("42", "42 R 0"),
        ("42 R 0", "42"),
        ("615", "615"),
    ],
)
def test_correct_answers_are_never_marked_wrong(given, expected):
    # This is the test that matters most in the whole suite.
    assert is_correct(given, expected), f"{given!r} should count as {expected!r}"


@pytest.mark.parametrize(
    "given, expected",
    [
        ("19 R 8", "19 R 7"),
        ("18 R 7", "19 R 7"),
        ("614", "615"),
        ("", "615"),
        ("weiss nicht", "615"),
        ("6150", "615"),
    ],
)
def test_wrong_answers_are_not_accepted(given, expected):
    assert not is_correct(given, expected)


def test_grade_flags_exactly_the_wrong_blanks():
    task = Task(
        id="1",
        kind="grid",
        render="…",
        blanks=[
            Blank(id="a", answer="240", label="60 · 4"),
            Blank(id="b", answer="180", label="60 · 3"),
            Blank(id="c", answer="300", label="60 · 5"),
        ],
    )
    result = grade(task, {"a": "240", "b": "190", "c": "300"})

    assert not result.all_correct
    assert [r.blank_id for r in result.wrong] == ["b"]
    assert result.wrong[0].label == "60 · 3"


def test_a_blank_left_empty_is_not_correct_but_is_reported_as_such():
    task = Task(id="1", kind="arith", render="…", blanks=[Blank(id="a", answer="7", label="3 + 4")])
    result = grade(task, {})
    assert result.wrong[0].given == ""
