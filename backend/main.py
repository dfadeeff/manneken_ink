import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.routes.chat import router as chat_router  # noqa: E402
from app.routes.learners import router as learners_router  # noqa: E402
from app.routes.meta import router as meta_router  # noqa: E402
from app.routes.speech import router as speech_router  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("manneken")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.dev_auth_bypass:
        log.warning("DEV_AUTH_BYPASS is on - every request is signed in as a test parent")
    from app.llm import router as llm

    configured = [name for name, ok in llm.configured_providers().items() if ok]
    if configured:
        log.info("model providers configured: %s", ", ".join(configured))
    else:
        log.warning("no model provider configured - the tutor will not be able to reply")
    yield


app = FastAPI(title="Manneken Tutor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta_router)
app.include_router(learners_router)
app.include_router(chat_router)
app.include_router(speech_router)
