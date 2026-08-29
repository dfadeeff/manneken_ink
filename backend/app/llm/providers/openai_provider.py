import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from .base import LLMResponse, ProviderError, ToolCall, Turn


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str):
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None

    def available(self) -> bool:
        return self._client is not None

    def _messages(self, system: str, turns: list[Turn]) -> list[dict]:
        return [{"role": "system", "content": system}] + [
            {"role": t.role, "content": t.content} for t in turns
        ]

    async def complete(self, *, model, system, turns, max_tokens, schema, spec) -> LLMResponse:
        if not self._client:
            raise ProviderError("openai: no API key configured")

        budget = max_tokens
        kwargs: dict = {"model": model, "messages": self._messages(system, turns)}
        if spec.reasoning_model:
            if spec.tier == "fast":
                # Triage and normalisation are lookups, not puzzles. Without this a
                # 64-token budget is spent entirely on hidden reasoning and the call
                # comes back empty - which silently disables the safety classifier.
                kwargs["reasoning_effort"] = "minimal"
                budget = max(max_tokens, 256)
            else:
                budget = max(max_tokens * 4, 2048)
        kwargs["max_completion_tokens"] = budget
        if schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema, "strict": True},
            }

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        text = choice.message.content or ""
        if not text.strip():
            if choice.finish_reason == "length":
                raise ProviderError(
                    f"openai: {model} hit the {budget}-token budget before writing output"
                )
            if schema:
                raise ProviderError("openai: empty structured response")
        usage = response.usage
        return LLMResponse(
            text=text,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )

    async def stream(self, *, model, system, turns, max_tokens, spec, usage) -> AsyncIterator[str]:
        if not self._client:
            raise ProviderError("openai: no API key configured")
        budget = max(max_tokens * 4, 2048) if spec.reasoning_model else max_tokens
        stream = await self._client.chat.completions.create(
            model=model,
            messages=self._messages(system, turns),
            max_completion_tokens=budget,
            stream=True,
            stream_options={"include_usage": True},
        )
        async for event in stream:
            if event.choices and event.choices[0].delta.content:
                yield event.choices[0].delta.content
            # The usage-bearing chunk arrives last and carries no choices.
            if event.usage:
                usage["input_tokens"] = event.usage.prompt_tokens or 0
                usage["output_tokens"] = event.usage.completion_tokens or 0

    # -- tool calling --------------------------------------------------------

    def _tool_schema(self, tools: list[dict]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for tool in tools
        ]

    def _wire_turns(self, system: str, turns: list[Turn]) -> list[dict]:
        messages: list[dict] = [{"role": "system", "content": system}]
        for turn in turns:
            if turn.tool_results:
                for result in turn.tool_results:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": result.call_id,
                            "content": json.dumps(result.content, ensure_ascii=False),
                        }
                    )
                continue

            message: dict = {"role": turn.role, "content": turn.content or None}
            if turn.tool_calls:
                message["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments, ensure_ascii=False),
                        },
                    }
                    for call in turn.tool_calls
                ]
            messages.append(message)
        return messages

    async def complete_with_tools(
        self, *, model, system, turns, max_tokens, tools, spec
    ) -> LLMResponse:
        if not self._client:
            raise ProviderError("openai: no API key configured")

        budget = max(max_tokens * 4, 2048) if spec.reasoning_model else max_tokens
        response = await self._client.chat.completions.create(
            model=model,
            messages=self._wire_turns(system, turns),
            max_completion_tokens=budget,
            tools=self._tool_schema(tools),
        )
        choice = response.choices[0]
        calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                # Never string-match serialised arguments; always parse.
                arguments=json.loads(call.function.arguments or "{}"),
            )
            for call in (choice.message.tool_calls or [])
        ]
        usage = response.usage
        return LLMResponse(
            text=choice.message.content or "",
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            tool_calls=calls,
        )
