"""Speech provider selection.

Same shape as the LLM router: call sites ask for speech, not for a vendor.
Only OpenAI is wired up today - it is the one provider whose key exists and
whose calls are verified. An ElevenLabs provider implementing the same
protocol drops in beside it without touching the routes.
"""

import logging

from ..config import get_settings
from .providers.base import SpeechError
from .providers.openai_speech import OpenAISpeech

log = logging.getLogger(__name__)


class SpeechRouter:
    def __init__(self):
        settings = get_settings()
        self._providers = [OpenAISpeech(settings.openai_api_key)]

    def _for(self, capability: str):
        for provider in self._providers:
            if getattr(provider, capability)():
                return provider
        return None

    def available(self) -> dict[str, bool]:
        return {
            "transcribe": self._for("can_transcribe") is not None,
            "speak": self._for("can_speak") is not None,
        }

    async def transcribe(self, *, audio: bytes, filename: str, language: str) -> str:
        provider = self._for("can_transcribe")
        if provider is None:
            raise SpeechError("no speech-to-text provider configured")
        return await provider.transcribe(audio=audio, filename=filename, language=language)

    async def speak(self, *, text: str, language: str, school_class: int) -> bytes:
        provider = self._for("can_speak")
        if provider is None:
            raise SpeechError("no text-to-speech provider configured")
        return await provider.speak(text=text, language=language, school_class=school_class)


speech = SpeechRouter()
