from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol


class ProviderError(RuntimeError):
    pass


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    tool_calls: list["ToolCall"] = field(default_factory=list)


@dataclass
class ToolResult:
    call_id: str
    name: str
    content: dict


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    content: str
    # Set on assistant turns that made tool calls, and on the results that follow.
    tool_calls: list["ToolCall"] = field(default_factory=list)
    tool_results: list["ToolResult"] = field(default_factory=list)


class Provider(Protocol):
    name: str

    def available(self) -> bool: ...

    async def complete(
        self,
        *,
        model: str,
        system: str,
        turns: list[Turn],
        max_tokens: int,
        schema: dict | None,
        spec,
    ) -> LLMResponse: ...

    def stream(
        self,
        *,
        model: str,
        system: str,
        turns: list[Turn],
        max_tokens: int,
        spec,
        usage: dict,
    ) -> AsyncIterator[str]:
        """Yield text chunks, then fill `usage` with input/output token counts.

        Streaming is where most of the spend happens, so it has to be priced like
        everything else - a router that cannot see the cost of its busiest call
        cannot route on cost.
        """
        ...
