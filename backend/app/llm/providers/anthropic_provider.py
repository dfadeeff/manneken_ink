import json
from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from .base import LLMResponse, ProviderError, Turn

REFUSAL_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = AsyncAnthropic(api_key=api_key) if api_key else None

    def available(self) -> bool:
        return self._client is not None

    def _kwargs(self, *, model, system, turns, max_tokens, spec, effort=None) -> dict:
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": t.role, "content": t.content} for t in turns],
        }
        # The 5-family rejects temperature outright, and effort only exists there.
        if spec.supports_effort and effort:
            kwargs["output_config"] = {"effort": effort}
        return kwargs

    async def complete(self, *, model, system, turns, max_tokens, schema, spec) -> LLMResponse:
        if not self._client:
            raise ProviderError("anthropic: no API key configured")

        # Short, structured work does not need deep reasoning; keep kids waiting less.
        effort = "low" if (schema or spec.tier == "fast") else "medium"
        kwargs = self._kwargs(
            model=model, system=system, turns=turns, max_tokens=max_tokens, spec=spec, effort=effort
        )
        if schema:
            kwargs.setdefault("output_config", {})
            kwargs["output_config"]["format"] = {"type": "json_schema", "schema": schema}

        if spec.needs_refusal_fallback:
            response = await self._client.beta.messages.create(
                betas=[REFUSAL_FALLBACK_BETA], fallbacks="default", **kwargs
            )
        else:
            response = await self._client.messages.create(**kwargs)

        if response.stop_reason == "refusal":
            raise ProviderError("anthropic: request refused by safety classifier")

        text = "".join(b.text for b in response.content if b.type == "text")
        if schema and not text.strip():
            raise ProviderError("anthropic: empty structured response")
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    async def stream(self, *, model, system, turns, max_tokens, spec, usage) -> AsyncIterator[str]:
        if not self._client:
            raise ProviderError("anthropic: no API key configured")
        kwargs = self._kwargs(
            model=model, system=system, turns=turns, max_tokens=max_tokens, spec=spec, effort="medium"
        )
        async with self._client.messages.stream(**kwargs) as stream:
            async for chunk in stream.text_stream:
                yield chunk
            final = await stream.get_final_message()
            usage["input_tokens"] = final.usage.input_tokens
            usage["output_tokens"] = final.usage.output_tokens
