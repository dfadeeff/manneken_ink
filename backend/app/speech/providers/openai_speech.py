from openai import AsyncOpenAI

from .base import SpeechError

# Steering the delivery matters more here than the voice does: the same words
# read briskly sound like a test, read slowly they sound like help.
DELIVERY = {
    "de": (
        "Sprich warm, ruhig und deutlich langsamer als normal, wie eine geduldige "
        "Grundschullehrerin zu einem {age}-jährigen Kind. Mache kleine Pausen zwischen "
        "den Sätzen. Bei Zahlen und Rechenschritten besonders langsam und deutlich."
    ),
    "en": (
        "Speak warmly, calmly and noticeably slower than normal, like a patient primary "
        "school teacher talking to a {age}-year-old child. Pause a little between "
        "sentences, and slow down further for numbers and calculation steps."
    ),
}


class OpenAISpeech:
    name = "openai"

    # gpt-4o-transcribe beats whisper-1 on children's speech, which is the whole
    # job here. gpt-4o-mini-tts is the only TTS model that accepts `instructions`.
    STT_MODEL = "gpt-4o-transcribe"
    TTS_MODEL = "gpt-4o-mini-tts"
    VOICE = "nova"

    def __init__(self, api_key: str):
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None

    def can_transcribe(self) -> bool:
        return self._client is not None

    def can_speak(self) -> bool:
        return self._client is not None

    async def transcribe(self, *, audio: bytes, filename: str, language: str) -> str:
        if not self._client:
            raise SpeechError("openai: no API key configured")
        result = await self._client.audio.transcriptions.create(
            model=self.STT_MODEL,
            file=(filename, audio),
            language=language,
            # Priming the vocabulary; children mumble numbers.
            prompt=(
                "Ein Kind übt Mathe und Deutsch."
                if language == "de"
                else "A child is practising maths and German."
            ),
        )
        return (result.text or "").strip()

    async def speak(self, *, text: str, language: str, school_class: int) -> bytes:
        if not self._client:
            raise SpeechError("openai: no API key configured")
        age = {2: 8, 3: 9, 4: 10}.get(school_class, 9)
        instructions = DELIVERY.get(language, DELIVERY["en"]).format(age=age)
        response = await self._client.audio.speech.create(
            model=self.TTS_MODEL,
            voice=self.VOICE,
            input=text,
            instructions=instructions,
            response_format="mp3",
        )
        return response.read()
