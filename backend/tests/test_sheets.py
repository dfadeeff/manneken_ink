import re

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.models import Learner, Parent
from app.tutor.exercises import generators, sheets


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def learner(db):
    parent = Parent(clerk_user_id="test_parent")
    db.add(parent)
    await db.commit()
    row = Learner(parent_id=parent.id, name="Lena", school_class=4, language="de")
    db.add(row)
    await db.commit()
    return row


async def _sheet(db, learner, topic="zahlenmauern"):
    return await sheets.start(
        db, learner_id=learner.id, session_id=None, topic_id=topic, count=3
    )


async def test_the_sheet_handed_to_the_model_contains_no_answers(db, learner):
    sheet = await _sheet(db, learner)
    blob = str(sheet)
    # It must carry the tasks and the blank names, and nothing that solves them.
    assert sheet["tasks"] and all(t["felder"] for t in sheet["tasks"])
    assert "answer" not in blob and "loesung" not in blob.lower()


async def test_hints_reveal_the_solution_only_at_level_three(db, learner):
    sheet = await _sheet(db, learner)

    first = await sheets.hint(db, learner_id=learner.id, sheet_id=sheet["sheet_id"], task="1")
    assert first["stufe"] == 1
    assert "loesungsweg" not in first

    second = await sheets.hint(db, learner_id=learner.id, sheet_id=sheet["sheet_id"], task="1")
    assert second["stufe"] == 2
    assert "loesungsweg" not in second

    third = await sheets.hint(db, learner_id=learner.id, sheet_id=sheet["sheet_id"], task="1")
    assert third["stufe"] == 3
    assert third["loesungsweg"]

    # And it does not climb past the top.
    fourth = await sheets.hint(db, learner_id=learner.id, sheet_id=sheet["sheet_id"], task="1")
    assert fourth["stufe"] == 3


async def test_checking_reports_which_blanks_are_wrong_without_giving_the_answer(db, learner):
    sheet = await _sheet(db, learner)
    rows = await sheets._rows(db, sheet["sheet_id"], learner.id)
    first = rows[0]
    truth = {b["id"]: b["answer"] for b in first.blanks}

    # One blank deliberately wrong.
    wrong_id = list(truth)[0]
    answers = {"1": dict(truth) | {wrong_id: "99999"}}
    result = await sheets.check(
        db, learner_id=learner.id, sheet_id=sheet["sheet_id"], answers=answers
    )

    assert result["falsche_aufgaben"] == ["1"]
    reported = result["ergebnisse"][0]["fehler"]
    assert [f["feld"] for f in reported] == [wrong_id]
    # The correct value must not appear anywhere in what the model is told.
    assert truth[wrong_id] not in str(result)


async def test_a_fully_correct_sheet_is_marked_solved(db, learner):
    sheet = await _sheet(db, learner)
    rows = await sheets._rows(db, sheet["sheet_id"], learner.id)
    answers = {
        str(row.position + 1): {b["id"]: b["answer"] for b in row.blanks} for row in rows
    }
    result = await sheets.check(
        db, learner_id=learner.id, sheet_id=sheet["sheet_id"], answers=answers
    )
    assert result["alles_richtig"]
    assert result["falsche_aufgaben"] == []


OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "·": lambda a, b: a * b,
}


def _recompute(label: str) -> str:
    """Work the stated sum out independently of the generator that produced it."""
    match = re.fullmatch(r"\s*(\d+)\s*([+\-·:])\s*(\d+)\s*", label)
    assert match, f"unparseable label {label!r}"
    left, op, right = int(match[1]), match[2], int(match[3])
    if op == ":":
        quotient, remainder = divmod(left, right)
        return f"{quotient} R {remainder}" if remainder else str(quotient)
    return str(OPS[op](left, right))


@pytest.mark.parametrize("topic", generators.generatable_topics())
@pytest.mark.parametrize("seed", [1, 7, 1234, 99999])
async def test_every_generated_answer_recomputes_to_the_same_value(topic, seed):
    """The generators must never state an answer that does not check out.

    Every blank whose label is a plain sum is worked out again here, by
    different code, and has to agree.
    """
    sheet = generators.build_sheet(topic, count=8, seed=seed)
    assert sheet.tasks

    checked = 0
    for task in sheet.tasks:
        for blank in task.blanks:
            assert blank.answer, f"{topic}/{task.id}/{blank.id} has no answer"
            if re.fullmatch(r"\s*\d+\s*[+\-·:]\s*\d+\s*", blank.label or ""):
                assert blank.answer == _recompute(blank.label), (
                    f"{topic}/{task.id}/{blank.id}: {blank.label} = {blank.answer}?"
                )
                checked += 1
    assert checked or topic == "zahlenmauern"


@pytest.mark.parametrize("seed", range(12))
async def test_pyramids_are_internally_consistent(seed):
    """Every pyramid must satisfy its own multiplication, in both directions."""
    sheet = generators.build_sheet("zahlenmauern", count=4, seed=seed)
    for task in sheet.tasks:
        # Rebuild the pyramid: given numbers where shown, answers where blank.
        answers = {b.id: int(b.answer) for b in task.blanks}
        rows = [line.split() for line in task.render.splitlines()]
        flat: list[int] = []
        for cell in [c for row in rows for c in row]:
            if cell.startswith("["):
                flat.append(answers[cell[1]])
            else:
                flat.append(int(cell))

        top, m1, m2, u1, u2, u3 = flat
        assert m1 == u1 * u2, f"{task.render}\n{m1} != {u1}·{u2}"
        assert m2 == u2 * u3, f"{task.render}\n{m2} != {u2}·{u3}"
        assert top == m1 * m2, f"{task.render}\n{top} != {m1}·{m2}"
