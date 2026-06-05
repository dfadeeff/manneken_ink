import io
import os
import json
import tempfile

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from .session import session, MOODS
from .prompts import chat_system_prompt, MOOD_VOICES

router = APIRouter(prefix="/api")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatRequest(BaseModel):
    message: str
    gender: str = "boy"
    mood: str = "happy"


class TTSRequest(BaseModel):
    message: str
    mood: str = "happy"
    gender: str = "boy"


def extract_mood(reply: str) -> tuple[str, str]:
    lines = reply.strip().split("\n")
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith("{") and "mood" in line:
            try:
                data = json.loads(line)
                mood = data.get("mood", "happy")
                if mood in MOODS:
                    return "\n".join(lines[:i]).strip(), mood
            except json.JSONDecodeError:
                pass
    return reply.strip(), "happy"


@router.post("/chat")
async def chat(req: ChatRequest):
    session.gender = req.gender
    session.mood = req.mood
    session.add_message("user", req.message)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": chat_system_prompt(req.gender, req.mood)}]
        + session.recent_messages(),
    )
    raw_reply = response.choices[0].message.content
    clean_reply, new_mood = extract_mood(raw_reply)
    session.add_message("assistant", clean_reply)
    session.mood = new_mood

    return {"reply": clean_reply, "mood": new_mood}


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    voice = MOOD_VOICES.get(req.mood, "nova")
    if req.gender == "girl" and voice == "onyx":
        voice = "shimmer"

    response = client.audio.speech.create(model="tts-1", voice=voice, input=req.message)
    return StreamingResponse(io.BytesIO(response.read()), media_type="audio/mpeg")


@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return {"text": transcript.text}
    finally:
        os.unlink(tmp_path)


@router.post("/reset")
async def reset_conversation():
    session.reset_chat()
    return {"status": "ok"}