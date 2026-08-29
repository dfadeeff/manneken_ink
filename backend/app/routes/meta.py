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
async def config(probe: bool = Query(False, description="Make one tiny real call per provider")):
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
