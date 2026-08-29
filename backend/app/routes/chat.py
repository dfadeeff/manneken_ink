import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_parent, owned_learner
from ..config import get_settings
from ..db import SessionLocal, get_db
from ..llm import NoModelAvailable, Turn, router as llm
from ..models import ChatSession, Learner, Message, Parent, SafetyFlag
from ..schemas import ChatIn, MessageOut, SessionIn, SessionOut
from ..tutor import guardrails, tools as tutor_tools
from ..tutor.prompts import system_prompt

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

settings = get_settings()
limiter = guardrails.RateLimiter(settings.messages_per_minute, settings.messages_per_day)

HISTORY_TURNS = 20

RATE_LIMIT_TEXT = {
    "too_fast": {
        "de": "Puh, das ging schnell! Lass uns kurz durchatmen und dann weitermachen.",
        "en": "Wow, that was quick! Let us take a short breath and carry on.",
    },
    "daily_cap": {
        "de": "Für heute haben wir schon richtig viel geübt. Morgen geht es weiter!",
        "en": "We have practised a lot today. Let us carry on tomorrow!",
    },
}


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionIn,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    await owned_learner(body.learner_id, parent, db)
    session = ChatSession(learner_id=body.learner_id, subject=body.subject, topic_id=body.topic_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: str,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    """The session is the source of truth for which learner is practising.

    sessionStorage is fine for handing a draft across the sign-in redirect, but
    it is empty in a new tab, so nothing load-bearing should depend on it.
    """
    return await _owned_session(session_id, parent, db)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def session_messages(
    session_id: str,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    session = await _owned_session(session_id, parent, db)
    rows = await db.scalars(
        select(Message).where(Message.session_id == session.id).order_by(Message.created_at)
    )
    return list(rows)


@router.post("/stream")
async def stream_reply(
    body: ChatIn,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    session = await _owned_session(body.session_id, parent, db)
    learner = await owned_learner(session.learner_id, parent, db)

    text = guardrails.sanitise(body.message, max_chars=settings.max_message_chars)
    if not text:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty message")

    history = list(
        await db.scalars(
            select(Message)
            .where(Message.session_id == session.id)
            .order_by(Message.created_at.desc())
            .limit(HISTORY_TURNS)
        )
    )
    history.reverse()

    # Snapshot what the generator needs; the request's DB session is gone by then.
    context = {
        "session_id": session.id,
        "learner_id": learner.id,
        "name": learner.name,
        "language": learner.language,
        "school_class": learner.school_class,
        "topic_id": session.topic_id,
        "history": [(m.role, m.content) for m in history],
    }

    return StreamingResponse(
        _generate(text, context),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _chunks(text: str, size: int = 24):
    """Hand the finished reply to the client in pieces so it still reads as it arrives."""
    for start in range(0, len(text), size):
        yield text[start : start + size]


async def _generate(text: str, ctx: dict) -> AsyncIterator[str]:
    language = ctx["language"]

    # Layer 1: perimeter.
    limited = limiter.check(ctx["learner_id"])
    if limited:
        reply = RATE_LIMIT_TEXT[limited][language]
        message_id = await _persist(ctx, text, reply, intercepted=True)
        yield _event({"type": "delta", "text": reply})
        yield _event({"type": "done", "intercepted": True, "message_id": message_id})
        return

    # Layer 2: triage. Distress and unsafe never reach the tutor model.
    category = await guardrails.triage(text, learner_id=ctx["learner_id"])
    if category in ("distress", "unsafe"):
        reply = guardrails.SAFE_REPLY[category][language]
        message_id = await _persist(ctx, text, reply, intercepted=True, flag=(category, text))
        yield _event({"type": "delta", "text": reply})
        yield _event({"type": "done", "intercepted": True, "message_id": message_id})
        return

    # Layers 3 and 5: constitution, plus child input fenced as data.
    system = system_prompt(
        name=ctx["name"],
        school_class=ctx["school_class"],
        language=language,
        topic_id=ctx["topic_id"],
        with_tools=True,
    )
    turns = [Turn(role=role, content=content) for role, content in ctx["history"]]
    turns.append(Turn(role="user", content=guardrails.wrap_child(text, language)))

    # The tutor runs a tool loop: worksheets are generated, marked and hinted by
    # deterministic Python, never by the model. That means the reply is complete
    # before we start sending it, so it is chunked to the client afterwards -
    # correctness here is worth more than time-to-first-token.
    async def run_tool(name: str, arguments: dict) -> dict:
        async with SessionLocal() as tool_db:
            return await tutor_tools.dispatch(
                name,
                arguments,
                db=tool_db,
                learner_id=ctx["learner_id"],
                session_id=ctx["session_id"],
                school_class=ctx["school_class"],
            )

    # Layer 4: nothing reaches the child unfiltered.
    cleaner = guardrails.StreamSanitiser()
    collected: list[str] = []
    try:
        answer = await llm.run_tools(
            "tutor_tools",
            system=system,
            turns=turns,
            tools=tutor_tools.TOOLS,
            execute=run_tool,
            max_tokens=700,
            learner_id=ctx["learner_id"],
        )
        for chunk in _chunks(answer):
            safe = cleaner.feed(chunk)
            if safe:
                collected.append(safe)
                yield _event({"type": "delta", "text": safe})
    except NoModelAvailable:
        log.error("no model could answer for learner %s", ctx["learner_id"], exc_info=True)
        outage = (
            "Ich kann dir gerade leider nicht antworten. Das liegt an mir, nicht an dir. "
            "Bitte sag einem Erwachsenen Bescheid und versuch es später nochmal."
            if language == "de"
            else "I cannot answer right now. That is my fault, not yours. "
            "Please tell a grown-up and try again later."
        )
        message_id = await _persist(ctx, text, outage, intercepted=True)
        yield _event({"type": "delta", "text": outage})
        yield _event({"type": "done", "intercepted": True, "message_id": message_id, "error": "no_model"})
        return
    except Exception:  # noqa: BLE001
        log.exception("tutor stream failed")
        oops = (
            "Ups, ich habe den Faden verloren. Sag es noch einmal?"
            if language == "de"
            else "Oops, I lost my train of thought. Could you say that again?"
        )
        yield _event({"type": "delta", "text": oops})
        yield _event({"type": "done", "intercepted": True})
        return

    tail = cleaner.flush()
    if tail:
        collected.append(tail)
        yield _event({"type": "delta", "text": tail})

    reply = "".join(collected).strip()
    review = guardrails.validate_output(reply, school_class=ctx["school_class"])
    issues = cleaner.issues + review.issues
    if issues:
        log.info("output issues for learner %s: %s", ctx["learner_id"], issues)

    message_id = await _persist(ctx, text, reply, intercepted=False)
    yield _event({"type": "done", "intercepted": False, "issues": issues, "message_id": message_id})


async def _persist(ctx, child_text, reply, *, intercepted, flag=None) -> str:
    async with SessionLocal() as db:
        db.add(Message(session_id=ctx["session_id"], role="user", content=child_text))
        assistant = Message(
            session_id=ctx["session_id"],
            role="assistant",
            content=reply,
            intercepted=intercepted,
        )
        db.add(assistant)
        if flag:
            category, excerpt = flag
            db.add(
                SafetyFlag(
                    learner_id=ctx["learner_id"],
                    session_id=ctx["session_id"],
                    category=category,
                    excerpt=excerpt[:500],
                )
            )
        await db.commit()
        return assistant.id


async def _owned_session(session_id: str, parent: Parent, db: AsyncSession) -> ChatSession:
    session = await db.scalar(
        select(ChatSession)
        .join(Learner, Learner.id == ChatSession.learner_id)
        .where(ChatSession.id == session_id, Learner.parent_id == parent.id)
    )
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session
