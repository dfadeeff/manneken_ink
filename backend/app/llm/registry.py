"""The model catalogue.

Every price below is per million tokens and was taken from the providers' own
pricing pages. Latency figures are seeds only - the router replaces them with
an observed moving average as soon as it has real calls to learn from.

Re-pointing a tier is a one-line edit here, or ROUTER_TIER_OVERRIDES in the env.
"""

from dataclasses import dataclass, field
from typing import Literal

Tier = Literal["fast", "standard", "strong"]


@dataclass(frozen=True)
class ModelSpec:
    provider: Literal["anthropic", "openai", "google"]
    model: str
    tier: Tier
    input_per_mtok: float
    output_per_mtok: float
    seed_latency_ms: int
    # Anthropic's 5-family rejects temperature/top_p outright (HTTP 400).
    supports_temperature: bool = True
    # output_config.effort - Anthropic 5-family and Opus 4.7+ only.
    supports_effort: bool = False
    # Opus 5 / Fable 5 can stop with stop_reason="refusal"; ask the server to
    # route around it rather than handing a child an empty reply.
    needs_refusal_fallback: bool = False
    # OpenAI's gpt-5 family spends max_completion_tokens on hidden reasoning
    # before it writes a single visible character. Budgets must allow for it.
    reasoning_model: bool = False
    tags: tuple[str, ...] = field(default=())

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.model}"

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * self.input_per_mtok + output_tokens * self.output_per_mtok
        ) / 1_000_000


# Ordered by preference within each tier. "balanced" honours this order.
CATALOGUE: list[ModelSpec] = [
    # fast - safety triage, answer normalisation, short classifications.
    ModelSpec("anthropic", "claude-haiku-4-5", "fast", 1.00, 5.00, 900),
    ModelSpec("openai", "gpt-5-mini", "fast", 0.25, 2.00, 900, reasoning_model=True),
    ModelSpec("openai", "gpt-5-nano", "fast", 0.05, 0.40, 700, reasoning_model=True),
    ModelSpec("google", "gemini-3.1-flash-lite", "fast", 0.25, 1.50, 800),

    # standard - the tutoring dialogue and exercise generation.
    ModelSpec(
        "anthropic", "claude-sonnet-5", "standard", 2.00, 10.00, 2500,
        supports_temperature=False, supports_effort=True,
    ),
    ModelSpec("google", "gemini-3.7-flash", "standard", 0.75, 3.75, 1800),
    ModelSpec("openai", "gpt-4.1", "standard", 2.00, 8.00, 2200),

    # strong - word problems, open-text grading, anything where being wrong costs a child.
    ModelSpec(
        "anthropic", "claude-opus-5", "strong", 5.00, 25.00, 5000,
        supports_temperature=False, supports_effort=True, needs_refusal_fallback=True,
    ),
    ModelSpec("google", "gemini-3.1-pro-preview", "strong", 2.00, 12.00, 4000),
    ModelSpec("openai", "gpt-5.5", "strong", 5.00, 30.00, 5000, reasoning_model=True),
]

BY_KEY = {spec.key: spec for spec in CATALOGUE}


def candidates(tier: Tier) -> list[ModelSpec]:
    return [spec for spec in CATALOGUE if spec.tier == tier]


def lookup(key: str) -> ModelSpec | None:
    return BY_KEY.get(key)
