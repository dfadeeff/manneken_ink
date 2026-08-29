"""The worksheet state machine.

This is the guardrail that a system prompt cannot provide. The tutor model is
never handed a task's answer. It can ask for a hint, and the hint it gets back
depends on how many times the child has already tried - so it *cannot* reveal
the solution on the first miss even if it wants to. Only at level 3, after the
child has genuinely worked at it, does the worked solution enter the model's
context at all.

Everything here is deterministic. The model's job is to be kind and clear about
results this module computed, never to compute them.
"""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import Attempt, Exercise, TopicMastery
from ..curriculum import BY_ID
from . import generators
from .grading import grade
from .models import Blank, Task

MAX_HINT_LEVEL = 3


async def start(
    db: AsyncSession, *, learner_id: str, session_id: str | None, topic_id: str, count: int = 6
) -> dict:
    """Generate a worksheet and store it. Returns only what the child should see."""
    sheet = generators.build_sheet(topic_id, count=count)
    sheet_id = uuid.uuid4().hex
    topic = BY_ID.get(topic_id)

    for position, task in enumerate(sheet.tasks):
        db.add(
            Exercise(
                learner_id=learner_id,
                session_id=session_id,
                sheet_id=sheet_id,
                subject=topic.subject if topic else "math",
                topic_id=topic_id,
                kind=task.kind,
                position=position,
                prompt=task.render,
                answer=json.dumps({b.id: b.answer for b in task.blanks}, ensure_ascii=False),
                blanks=[{"id": b.id, "answer": b.answer, "label": b.label} for b in task.blanks],
                hints=task.solution,
                source="python",
            )
        )
    await db.commit()

    return {
        "sheet_id": sheet_id,
        "title": sheet.title,
        "instruction": sheet.instruction,
        "tasks": [
            {"task": task.id, "aufgabe": task.render, "felder": [b.id for b in task.blanks]}
            for task in sheet.tasks
        ],
    }


async def _rows(db: AsyncSession, sheet_id: str, learner_id: str) -> list[Exercise]:
    return list(
        await db.scalars(
            select(Exercise)
            .where(Exercise.sheet_id == sheet_id, Exercise.learner_id == learner_id)
            .order_by(Exercise.position)
        )
    )


def _as_task(row: Exercise) -> Task:
    return Task(
        id=str(row.position + 1),
        kind=row.kind,
        render=row.prompt,
        blanks=[Blank(id=b["id"], answer=b["answer"], label=b.get("label", "")) for b in row.blanks],
        solution=list(row.hints or []),
    )


async def check(
    db: AsyncSession, *, learner_id: str, sheet_id: str, answers: dict[str, dict[str, str]]
) -> dict:
    """Mark the child's work.

    Reports which blanks are wrong and what each one was asking, and never the
    right answer - that only ever arrives through the hint ladder.
    """
    rows = await _rows(db, sheet_id, learner_id)
    if not rows:
        return {"error": "Dieses Aufgabenblatt gibt es nicht."}

    by_number = {str(row.position + 1): row for row in rows}
    summary, correct_count, total = [], 0, 0

    for number, row in by_number.items():
        given = answers.get(number) or {}
        if not given:
            continue

        task = _as_task(row)
        result = grade(task, given)
        total += len(result.results)
        correct_count += sum(1 for r in result.results if r.correct)

        attempt_no = row.hint_level + 1
        for blank_result in result.results:
            db.add(
                Attempt(
                    exercise_id=row.id,
                    learner_id=learner_id,
                    attempt_no=attempt_no,
                    blank_id=blank_result.blank_id,
                    given=blank_result.given,
                    correct=blank_result.correct,
                    graded_by="exact",
                )
            )

        if result.all_correct:
            row.solved = True
        summary.append(
            {
                "task": number,
                "richtig": result.all_correct,
                "fehler": [
                    {"feld": r.blank_id, "gefragt": r.label, "geschrieben": r.given or "(leer)"}
                    for r in result.wrong
                ],
            }
        )

    await _update_mastery(db, learner_id, rows[0].topic_id, correct_count, total)
    await db.commit()

    wrong_tasks = [entry["task"] for entry in summary if not entry["richtig"]]
    return {
        "geprueft": len(summary),
        "alles_richtig": not wrong_tasks,
        "falsche_aufgaben": wrong_tasks,
        "ergebnisse": summary,
    }


async def hint(db: AsyncSession, *, learner_id: str, sheet_id: str, task: str) -> dict:
    """Advance the hint ladder by exactly one step and return only that step."""
    rows = await _rows(db, sheet_id, learner_id)
    row = next((r for r in rows if str(r.position + 1) == str(task)), None)
    if row is None:
        return {"error": "Diese Aufgabe gibt es auf dem Blatt nicht."}
    if row.solved:
        return {"stufe": 0, "hinweis": "Diese Aufgabe ist schon gelöst."}

    row.hint_level = min(row.hint_level + 1, MAX_HINT_LEVEL)
    level = row.hint_level
    steps = list(row.hints or [])
    await db.commit()

    if level == 1:
        labels = [b.get("label", "") for b in row.blanks if b.get("label")]
        return {
            "stufe": 1,
            "art": "anstupsen",
            "schau_dir_an": labels[:2],
            "hinweis": "Nenne dem Kind, worauf es schauen soll. Verrate noch nichts.",
        }
    if level == 2:
        return {
            "stufe": 2,
            "art": "strategie",
            "erster_schritt": steps[0] if steps else "",
            "hinweis": "Zeige nur diesen ersten Schritt. Das Ergebnis noch nicht.",
        }
    return {
        "stufe": 3,
        "art": "gemeinsam_rechnen",
        "loesungsweg": steps,
        "hinweis": "Jetzt gemeinsam Schritt für Schritt durchrechnen, freundlich und ohne Tadel.",
    }


async def _update_mastery(
    db: AsyncSession, learner_id: str, topic_id: str, correct: int, total: int
) -> None:
    if not total:
        return
    row = await db.scalar(
        select(TopicMastery).where(
            TopicMastery.learner_id == learner_id, TopicMastery.topic_id == topic_id
        )
    )
    share = correct / total
    if row is None:
        db.add(TopicMastery(learner_id=learner_id, topic_id=topic_id, score=share, attempts=total))
    else:
        # Rolling average, weighted towards recent work.
        row.score = row.score * 0.7 + share * 0.3
        row.attempts += total
