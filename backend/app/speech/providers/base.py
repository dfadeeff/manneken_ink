from typing import Protocol


class SpeechError(RuntimeError):
    pass


class SpeechProvider(Protocol):
    name: str

    def can_transcribe(self) -> bool: ...

    def can_speak(self) -> bool: ...

    async def transcribe(self, *, audio: bytes, filename: str, language: str) -> str: ...

    async def speak(self, *, text: str, language: str, school_class: int) -> bytes: ...
