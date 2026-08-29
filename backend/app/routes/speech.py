"""Voice in and out.

Two deliberate constraints:

* Transcription only returns text. The caller then posts it to /api/chat/stream
  like anything typed, so speaking to Mika goes through exactly the same
  guardrail pipeline as typing to her - voice is not a way around triage.
* Synthesis takes a message id, never free text. The endpoint can only voice
  something Mika already said and already validated, so it cannot be used to
  make the app read out arbitrary content, or as a free TTS oracle.
"""

import io
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_parent, owned_learner
from ..config import get_settings
from ..db import get_db
from ..models import ChatSession, Learner, Message, Parent
from ..speech import SpeechError, speech
from ..tutor import guardrails

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/speech", tags=["speech"])

settings = get_settings()
# Voice is metered separately from chat: a held mic button is easy to abuse.
limiter = guardrails.RateLimiter(per_minute=12, per_day=300)

MAX_AUDIO_BYTES = 8 * 1024 * 1024  # ~ a few minutes of webm/opus
ALLOWED_SUFFIXES = ("webm", "mp4", "m4a", "mp3", "wav", "ogg")


class SpeakIn(BaseModel):
    message_id: str


@router.get("/status")
async def status_(parent: Parent = Depends(current_parent)):
    return speech.available()


@router.post("/transcribe")
async def transcribe(
    learner_id: str = Form(...),
    file: UploadFile = File(...),
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    learner = await owned_learner(learner_id, parent, db)

    if limiter.check(learner.id):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Zu viele Aufnahmen")

    audio = await file.read()
    if not audio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty recording")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Recording too long")

    suffix = (file.filename or "audio.webm").rsplit(".", 1)[-1].lower()
    if suffix not in ALLOWED_SUFFIXES:
        suffix = "webm"

    try:
        text = await speech.transcribe(
            audio=audio, filename=f"audio.{suffix}", language=learner.language
        )
    except SpeechError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("transcription failed")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Transcription failed") from exc

    # Same sanitising the typed path gets. Triage happens downstream in /chat/stream.
    return {"text": guardrails.sanitise(text, max_chars=settings.max_message_chars)}


@router.post("/speak")
async def speak(
    body: SpeakIn,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        select(Message, Learner)
        .join(ChatSession, ChatSession.id == Message.session_id)
        .join(Learner, Learner.id == ChatSession.learner_id)
        .where(Message.id == body.message_id, Learner.parent_id == parent.id)
    )
    found = row.first()
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")

    message, learner = found
    if message.role != "assistant":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only Mika's own replies are spoken")

    try:
        audio = await speech.speak(
            text=message.content,
            language=learner.language,
            school_class=learner.school_class,
        )
    except SpeechError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("speech synthesis failed")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Speech failed") from exc

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )
