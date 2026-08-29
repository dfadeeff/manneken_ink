from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from .base import LLMResponse, ProviderError, Turn


class GeminiProvider:
    name = "google"

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key) if api_key else None

    def available(self) -> bool:
        return self._client is not None

    def _contents(self, turns: list[Turn]) -> list[types.Content]:
        # Gemini calls the assistant role "model".
        return [
            types.Content(
                role="model" if t.role == "assistant" else "user",
                parts=[types.Part.from_text(text=t.content)],
            )
            for t in turns
        ]

    def _config(self, system: str, max_tokens: int, schema: dict | None) -> types.GenerateContentConfig:
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        )
        if schema:
            config.response_mime_type = "application/json"
            config.response_schema = schema
        return config

    async def complete(self, *, model, system, turns, max_tokens, schema, spec) -> LLMResponse:
        if not self._client:
            raise ProviderError("google: no API key configured")

        response = await self._client.aio.models.generate_content(
            model=model,
            contents=self._contents(turns),
            config=self._config(system, max_tokens, schema),
        )
        text = response.text or ""
        if schema and not text.strip():
            raise ProviderError("google: empty structured response")
        usage = response.usage_metadata
        return LLMResponse(
            text=text,
            input_tokens=(usage.prompt_token_count if usage else 0) or 0,
            output_tokens=(usage.candidates_token_count if usage else 0) or 0,
        )

    async def stream(self, *, model, system, turns, max_tokens, spec, usage) -> AsyncIterator[str]:
        if not self._client:
            raise ProviderError("google: no API key configured")
        stream = await self._client.aio.models.generate_content_stream(
            model=model,
            contents=self._contents(turns),
            config=self._config(system, max_tokens, None),
        )
        async for event in stream:
            if event.text:
                yield event.text
            if event.usage_metadata:
                usage["input_tokens"] = event.usage_metadata.prompt_token_count or 0
                usage["output_tokens"] = event.usage_metadata.candidates_token_count or 0
