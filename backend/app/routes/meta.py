import time

from fastapi import APIRouter, HTTPException, Query, status

from ..config import get_settings
from ..llm import Turn, router as llm
from ..llm.router import TASK_TIERS
from ..speech import speech

router = APIRouter(tags=["meta"])

_last_probe = float("-inf")
PROBE_COOLDOWN = 20.0


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/config")
async def config(
    probe: bool = Query(False, description="Make one tiny real call per provider"),
    tools: bool = Query(False, description="Also exercise the tool-calling path the tutor uses"),
):
    """What the server can actually do right now.

    `?probe=1` answers the question the plain response cannot: a key that is
    *present* is not the same as a key that *works*. A revoked key looks
    perfectly healthy here until something actually calls it.
    """
    settings = get_settings()
    providers = llm.configured_providers()
    payload = {
        "environment": settings.environment,
        "providers": providers,
        "any_provider": any(providers.values()),
        "router_policy": settings.router_policy,
        "auth": "dev_bypass" if settings.dev_auth_bypass else "clerk",
        "speech": speech.available(),
        "plan": {task: [spec.key for spec in llm.plan(task)] for task in TASK_TIERS},
    }

    if probe:
        global _last_probe
        now = time.monotonic()
        if now - _last_probe < PROBE_COOLDOWN:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"probe is rate limited to once every {int(PROBE_COOLDOWN)}s",
            )
        _last_probe = now
        payload["probe"] = await _probe()
        if tools:
            payload["probe_tools"] = await _probe_tools()

    return payload


async def _probe() -> dict:
    """One minimal call per configured provider, reporting the real error text."""
    results = {}
    for name, provider in llm._providers.items():  # noqa: SLF001 - diagnostics
        if not provider.available():
            results[name] = "not configured"
            continue
        spec = next((s for s in llm.plan("tutor_tools") if s.provider == name), None)
        spec = spec or next((s for s in llm.plan("safety_triage") if s.provider == name), None)
        if spec is None:
            results[name] = "no model in the catalogue"
            continue
        try:
            await provider.complete(
                model=spec.model,
                system="Reply with the single word: ok",
                turns=[Turn(role="user", content="ok")],
                max_tokens=16,
                schema=None,
                spec=spec,
            )
            results[name] = f"ok ({spec.model})"
        except Exception as exc:  # noqa: BLE001 - the message is the whole point
            results[name] = f"FAILED ({spec.model}): {type(exc).__name__}: {str(exc)[:200]}"
    return results


async def _probe_tools() -> dict:
    """Exercise complete_with_tools with the tutor's real schema.

    A provider whose plain completion works can still fail here - a rejected
    tool schema, a wire-format mistake - and that failure is invisible to the
    ordinary probe while making every tutor turn fall back to an error.
    """
    from ..tutor.tools import TOOLS

    results = {}
    for spec in llm.plan("tutor_tools"):
        provider = llm._providers[spec.provider]  # noqa: SLF001 - diagnostics
        if not hasattr(provider, "complete_with_tools"):
            results[spec.key] = "provider has no tool support"
            continue
        try:
            response = await provider.complete_with_tools(
                model=spec.model,
                system="You are a maths tutor for a child in class 4. Use your tools.",
                turns=[Turn(role="user", content="Ich moechte Malpyramiden ueben")],
                max_tokens=200,
                tools=TOOLS,
                spec=spec,
            )
            called = [c.name for c in response.tool_calls]
            results[spec.key] = f"ok - tool_calls={called or 'none'}"
        except Exception as exc:  # noqa: BLE001 - the message is the whole point
            results[spec.key] = f"FAILED: {type(exc).__name__}: {str(exc)[:400]}"
    return results
