from fastapi import APIRouter

from ..config import get_settings
from ..llm import router as llm
from ..llm.router import TASK_TIERS

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/config")
async def config():
    """What the server can actually do right now - useful when a key is missing."""
    settings = get_settings()
    providers = llm.configured_providers()
    return {
        "environment": settings.environment,
        "providers": providers,
        "any_provider": any(providers.values()),
        "router_policy": settings.router_policy,
        "auth": "dev_bypass" if settings.dev_auth_bypass else "clerk",
        "plan": {task: [spec.key for spec in llm.plan(task)] for task in TASK_TIERS},
    }
