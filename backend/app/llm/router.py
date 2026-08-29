"""Task -> tier -> model routing across Anthropic, OpenAI and Gemini.

Call sites name a *task*, never a model. Tiers map to an ordered list of
candidates in registry.py; the policy decides how that list is sorted, and the
router walks it until one answers. Every call is timed, priced and logged, and
the observed latency feeds back into the "speed" policy.
"""

import json
import logging
import time
from collections.abc import AsyncIterator

from ..config import get_settings
from ..db import SessionLocal
from ..models import LLMCall
from .providers import AnthropicProvider, GeminiProvider, OpenAIProvider
from .providers.base import LLMResponse, ProviderError, Turn
from .registry import BY_KEY, ModelSpec, Tier, candidates

log = logging.getLogger(__name__)

# Which tier each task runs on. Adding a task means adding a line here, not a
# model id somewhere in the business logic.
TASK_TIERS: dict[str, Tier] = {
    "safety_triage": "fast",
    "answer_normalise": "fast",
    "tutor_reply": "standard",
    "exercise_generate": "standard",
    "hint_generate": "standard",
    "word_problem": "strong",
    "open_text_grade": "strong",
}

# Blended price assuming roughly 3:1 input:output, which is what a tutoring
# turn actually looks like. Used only for ordering under the "cost" policy.
def _blended(spec: ModelSpec) -> float:
    return spec.input_per_mtok * 0.75 + spec.output_per_mtok * 0.25


class NoModelAvailable(RuntimeError):
    pass


class LLMRouter:
    def __init__(self):
        settings = get_settings()
        self._settings = settings
        self._providers = {
            "anthropic": AnthropicProvider(settings.anthropic_api_key),
            "openai": OpenAIProvider(settings.openai_api_key),
            "google": GeminiProvider(settings.gemini_api_key),
        }
        self._observed_ms: dict[str, float] = {}

    # -- selection ---------------------------------------------------------

    def _latency(self, spec: ModelSpec) -> float:
        return self._observed_ms.get(spec.key, float(spec.seed_latency_ms))

    def plan(self, task: str) -> list[ModelSpec]:
        tier = TASK_TIERS.get(task, "standard")

        override = self._settings.tier_overrides.get(tier)
        pool = candidates(tier)
        if override and override in BY_KEY:
            pinned = BY_KEY[override]
            pool = [pinned] + [s for s in pool if s.key != pinned.key]

        usable = [s for s in pool if self._providers[s.provider].available()]

        policy = self._settings.router_policy
        if policy == "cost":
            usable.sort(key=_blended)
        elif policy == "speed":
            usable.sort(key=self._latency)
        # "balanced" keeps the catalogue's declared preference order.

        if override and override in BY_KEY:
            pinned = BY_KEY[override]
            if self._providers[pinned.provider].available():
                usable = [pinned] + [s for s in usable if s.key != pinned.key]
        return usable

    def configured_providers(self) -> dict[str, bool]:
        return {name: p.available() for name, p in self._providers.items()}

    # -- calling -----------------------------------------------------------

    async def complete(
        self,
        task: str,
        *,
        system: str,
        turns: list[Turn],
        schema: dict | None = None,
        max_tokens: int = 1024,
        learner_id: str | None = None,
    ) -> LLMResponse:
        plan = self.plan(task)
        if not plan:
            raise NoModelAvailable(
                f"no provider configured for task {task!r} - set at least one API key"
            )

        last_error: Exception | None = None
        for spec in plan:
            provider = self._providers[spec.provider]
            started = time.perf_counter()
            try:
                response = await provider.complete(
                    model=spec.model,
                    system=system,
                    turns=turns,
                    max_tokens=max_tokens,
                    schema=schema,
                    spec=spec,
                )
            except Exception as exc:  # noqa: BLE001 - any provider failure falls through
                elapsed = int((time.perf_counter() - started) * 1000)
                last_error = exc
                log.warning("llm %s failed on %s: %s", task, spec.key, exc)
                await self._record(spec, task, learner_id, 0, 0, elapsed, ok=False, error=str(exc))
                continue

            elapsed = int((time.perf_counter() - started) * 1000)
            self._observe(spec, elapsed)
            await self._record(
                spec, task, learner_id,
                response.input_tokens, response.output_tokens, elapsed, ok=True,
            )
            return response

        raise NoModelAvailable(f"every candidate failed for task {task!r}") from last_error

    async def complete_json(self, task: str, *, schema: dict, **kwargs) -> dict:
        response = await self.complete(task, schema=schema, **kwargs)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"malformed JSON for task {task!r}") from exc

    async def stream(
        self,
        task: str,
        *,
        system: str,
        turns: list[Turn],
        max_tokens: int = 1024,
        learner_id: str | None = None,
    ) -> AsyncIterator[str]:
        plan = self.plan(task)
        if not plan:
            raise NoModelAvailable(
                f"no provider configured for task {task!r} - set at least one API key"
            )

        for index, spec in enumerate(plan):
            provider = self._providers[spec.provider]
            started = time.perf_counter()
            produced = False
            usage: dict[str, int] = {}
            try:
                async for chunk in provider.stream(
                    model=spec.model,
                    system=system,
                    turns=turns,
                    max_tokens=max_tokens,
                    spec=spec,
                    usage=usage,
                ):
                    produced = True
                    yield chunk
            except Exception as exc:  # noqa: BLE001
                elapsed = int((time.perf_counter() - started) * 1000)
                await self._record(spec, task, learner_id, 0, 0, elapsed, ok=False, error=str(exc))
                log.warning("llm stream %s failed on %s: %s", task, spec.key, exc)
                # Once bytes are on the wire we cannot silently switch models -
                # the child would see two half-answers stitched together.
                if produced or index == len(plan) - 1:
                    raise
                continue

            elapsed = int((time.perf_counter() - started) * 1000)
            self._observe(spec, elapsed)
            await self._record(
                spec, task, learner_id,
                usage.get("input_tokens", 0), usage.get("output_tokens", 0), elapsed, ok=True,
            )
            return

    # -- telemetry ---------------------------------------------------------

    def _observe(self, spec: ModelSpec, elapsed_ms: int) -> None:
        previous = self._observed_ms.get(spec.key, float(spec.seed_latency_ms))
        self._observed_ms[spec.key] = previous * 0.8 + elapsed_ms * 0.2

    async def _record(
        self, spec, task, learner_id, input_tokens, output_tokens, latency_ms, *, ok, error=None
    ) -> None:
        try:
            async with SessionLocal() as session:
                session.add(
                    LLMCall(
                        learner_id=learner_id,
                        task=task,
                        tier=spec.tier,
                        provider=spec.provider,
                        model=spec.model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_usd=spec.cost(input_tokens, output_tokens),
                        latency_ms=latency_ms,
                        ok=ok,
                        error=error,
                    )
                )
                await session.commit()
        except Exception:  # noqa: BLE001 - telemetry must never break a lesson
            log.exception("failed to record llm telemetry")


router = LLMRouter()
