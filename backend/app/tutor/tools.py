"""The tutor's tools.

Design follows two rules from the agent-engineering notes:

* Anything the server can look up is not a model parameter. The learner, the
  school class and the active sheet are all inferred from the turn's context,
  so the model cannot pass the wrong one and cannot waste context carrying it.
* Tool results are the smallest useful JSON. Notably, results never contain a
  correct answer - checking says *which* blanks are wrong and what each asked
  for, and the answer only ever arrives through the gated hint ladder.
"""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Exercise
from .curriculum import BY_ID, for_class
from .exercises import sheets
from .exercises.generators import TOPIC_SHEETS

log = logging.getLogger(__name__)

TOOLS = [
    {
        "name": "sheet_start",
        "description": (
            "Start a new worksheet on one topic and show it to the child. "
            "Use when the child wants to practise, or asks for exercises."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": sorted(TOPIC_SHEETS),
                    "description": "Which topic to practise.",
                },
                "count": {
                    "type": "integer",
                    "minimum": 2,
                    "maximum": 8,
                    "description": "How many tasks. Default 6.",
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
    {
        "name": "sheet_check",
        "description": (
            "Check the child's answers to the current worksheet and report which are "
            "wrong. ALWAYS use this before saying whether an answer is right. "
            "Never judge an answer yourself."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "answers": {
                    "type": "object",
                    "description": (
                        'Answers keyed by task number, then by field letter. '
                        'For a task with one field use "a". '
                        'Example: {"1": {"a": "615"}, "2": {"a": "94 R 1"}}'
                    ),
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                }
            },
            "required": ["answers"],
            "additionalProperties": False,
        },
    },
    {
        "name": "sheet_hint",
        "description": (
            "Get the next hint for one task. The hint gets more concrete each time it "
            "is called: a nudge, then a strategy, then the worked solution. "
            "Use it instead of explaining the answer yourself."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": 'Task number, e.g. "3".'}
            },
            "required": ["task"],
            "additionalProperties": False,
        },
    },
]


async def _active_sheet_id(db: AsyncSession, learner_id: str) -> str | None:
    """The sheet the child is working on. Never a model parameter."""
    return await db.scalar(
        select(Exercise.sheet_id)
        .where(Exercise.learner_id == learner_id)
        .order_by(Exercise.created_at.desc())
        .limit(1)
    )


async def dispatch(
    name: str, arguments: dict, *, db: AsyncSession, learner_id: str, session_id: str | None,
    school_class: int,
) -> dict:
    """Run one tool call. Always returns a dict; never raises into the model loop."""
    try:
        if name == "sheet_start":
            topic = arguments.get("topic", "")
            if topic not in TOPIC_SHEETS:
                allowed = [t.id for t in for_class(school_class, "math") if t.id in TOPIC_SHEETS]
                return {"fehler": "Dieses Thema kann ich nicht üben.", "moegliche_themen": allowed}
            return await sheets.start(
                db,
                learner_id=learner_id,
                session_id=session_id,
                topic_id=topic,
                count=int(arguments.get("count") or 6),
            )

        sheet_id = await _active_sheet_id(db, learner_id)
        if not sheet_id:
            return {"fehler": "Es gibt gerade kein Aufgabenblatt. Starte zuerst eines."}

        if name == "sheet_check":
            answers = arguments.get("answers") or {}
            if isinstance(answers, str):  # some models stringify nested objects
                answers = json.loads(answers)
            return await sheets.check(
                db, learner_id=learner_id, sheet_id=sheet_id, answers=answers
            )

        if name == "sheet_hint":
            return await sheets.hint(
                db, learner_id=learner_id, sheet_id=sheet_id, task=str(arguments.get("task", ""))
            )

        return {"fehler": f"Unbekanntes Werkzeug {name}"}
    except Exception:  # noqa: BLE001 - a broken tool must not break the lesson
        log.exception("tool %s failed", name)
        return {"fehler": "Das hat gerade nicht geklappt."}


def topic_hint_for_prompt(school_class: int) -> str:
    ids = [t.id for t in for_class(school_class, "math") if t.id in TOPIC_SHEETS]
    labels = ", ".join(f"{i} ({BY_ID[i].de})" for i in ids if i in BY_ID)
    return labels
