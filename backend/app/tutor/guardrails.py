"""The guardrail layers.

Layers 1, 2 (deterministic half) and 5 are plain Python and cannot be argued
out of by anything a child types or a model generates. Layer 2's nuanced half
and layer 3 live in prompts.py; layer 4 is validate_output below.
"""

import logging
import re
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass, field

from ..llm import Turn, router
from .prompts import MAX_WORDS_BY_CLASS, TRIAGE_PROMPT

log = logging.getLogger(__name__)

Category = str  # "on_topic" | "off_topic" | "distress" | "unsafe"

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["on_topic", "off_topic", "distress", "unsafe"],
        }
    },
    "required": ["category"],
    "additionalProperties": False,
}

# High-precision only. Anything ambiguous is left to the model, because wrongly
# telling a child to go find an adult is its own small harm.
HARD_SIGNALS: dict[Category, tuple[str, ...]] = {
    "distress": (
        "ich will sterben", "ich will nicht mehr leben", "ich möchte sterben",
        "ich bringe mich um", "mich umbringen", "tut mir weh zu hause",
        "schlägt mich", "hat mich geschlagen", "ich ritze",
        "i want to die", "i want to kill myself", "kill myself",
        "hurt myself", "cutting myself", "hits me", "beats me",
    ),
    "unsafe": (
        "nacktbild", "nacktfoto", "schick mir ein bild von dir",
        "nude photo", "send nudes", "sexual",
    ),
}

SAFE_REPLY: dict[Category, dict[str, str]] = {
    "distress": {
        "de": (
            "Danke, dass du mir das sagst. Das klingt wichtig.\n"
            "Ich bin nur ein Lernhelfer und kann dir dabei nicht richtig helfen.\n"
            "Bitte erzähl es einem Erwachsenen, dem du vertraust – Mama, Papa, "
            "einer Lehrerin oder jemandem in deiner Familie.\n"
            "Wenn du magst, üben wir gleich weiter."
        ),
        "en": (
            "Thank you for telling me. That sounds important.\n"
            "I am only a learning helper, so I cannot help you properly with this.\n"
            "Please tell a grown-up you trust – a parent, a teacher, or someone in your family.\n"
            "When you are ready, we can carry on practising."
        ),
    },
    "unsafe": {
        "de": (
            "Darüber kann ich nicht sprechen. Wenn dich etwas beunruhigt, "
            "sag es bitte einem Erwachsenen, dem du vertraust.\n"
            "Sollen wir weiter üben?"
        ),
        "en": (
            "I cannot talk about that. If something is worrying you, please tell "
            "a grown-up you trust.\nShall we carry on practising?"
        ),
    },
    "off_topic": {
        "de": "Das klingt spannend! Aber gerade üben wir. Sollen wir weitermachen?",
        "en": "That sounds fun! But we are practising right now. Shall we carry on?",
    },
}

URL_RE = re.compile(r"\b(?:https?://|www\.)\S+|\b[\w.-]+\.(?:com|de|net|org|io|ai)\b", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
# Deliberately narrow: must start "+49..." or "0...". A bare run of digits is far
# more likely to be a written subtraction than a phone number.
PHONE_RE = re.compile(r"(?<![\d,.])(?:\+\d{1,3}[\s/-]?\d|0\d)(?:[\s/-]?\d){6,12}(?![\d,.])")
SENTENCE_RE = re.compile(r"[^.!?\n]+")

SHAMING_RE = re.compile(
    r"\b(dumm|blöd|falsch gemacht|das ist doch einfach|stupid|silly mistake|obviously|"
    r"you should know)\b",
    re.I,
)

INJECTION_RE = re.compile(
    r"(ignor(e|iere)\s+(all(e[nr]?)?\s+)?(previous|vorherige[nr]?|die)\s+\w+|"
    r"system\s*prompt|du bist (jetzt|ab sofort)|you are now|"
    r"vergiss (alle|deine) (regeln|anweisungen)|forget (all )?your (rules|instructions))",
    re.I,
)


# -- layer 1: perimeter ----------------------------------------------------


class RateLimiter:
    """Per-learner sliding window. Process-local, which is the right scope for a
    single Railway service; move to Redis if this ever runs on more than one."""

    def __init__(self, per_minute: int, per_day: int):
        self._per_minute = per_minute
        self._per_day = per_day
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, learner_id: str) -> str | None:
        now = time.monotonic()
        hits = self._hits[learner_id]
        while hits and now - hits[0] > 86_400:
            hits.popleft()

        recent = sum(1 for t in hits if now - t <= 60)
        if recent >= self._per_minute:
            return "too_fast"
        if len(hits) >= self._per_day:
            return "daily_cap"
        hits.append(now)
        return None


# -- layer 5: injection containment ---------------------------------------


def sanitise(text: str, *, max_chars: int) -> str:
    """Normalise, strip control characters, cap length."""
    text = unicodedata.normalize("NFC", text)
    text = "".join(ch for ch in text if ch == "\n" or unicodedata.category(ch)[0] != "C")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars]


def wrap_child(text: str, language: str) -> str:
    """Fence child input as data. Angle brackets are escaped so nothing typed can
    close the fence and start issuing instructions."""
    tag = "kind" if language == "de" else "child"
    fenced = text.replace("<", "‹").replace(">", "›")
    return f"<{tag}>{fenced}</{tag}>"


def looks_like_injection(text: str) -> bool:
    return bool(INJECTION_RE.search(text))


# -- layer 2: triage -------------------------------------------------------


def deterministic_triage(text: str) -> Category | None:
    lowered = text.lower()
    for category, phrases in HARD_SIGNALS.items():
        if any(phrase in lowered for phrase in phrases):
            return category
    return None


async def triage(text: str, *, learner_id: str | None = None) -> Category:
    hard = deterministic_triage(text)
    if hard:
        return hard

    try:
        result = await router.complete_json(
            "safety_triage",
            system=TRIAGE_PROMPT,
            turns=[Turn(role="user", content=text)],
            schema=TRIAGE_SCHEMA,
            max_tokens=256,
            learner_id=learner_id,
        )
    except Exception:  # noqa: BLE001
        # Fail open: a child mid-lesson should not be stonewalled because a
        # classifier broke. But say so loudly - the deterministic layer is the
        # only thing standing up while this is happening.
        log.error("safety triage unavailable, falling back to on_topic", exc_info=True)
        return "on_topic"

    category = result.get("category")
    return category if category in {"on_topic", "off_topic", "distress", "unsafe"} else "on_topic"


# -- layer 4: output validation -------------------------------------------


@dataclass
class OutputReview:
    text: str
    issues: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.issues


def validate_output(text: str, *, school_class: int) -> OutputReview:
    """Strip anything a child should never be handed, and report style problems.

    Contact details are removed outright. Long sentences and shaming language are
    reported but not rewritten - silently mangling a tutor's explanation is worse
    than logging that the prompt needs work.
    """
    issues: list[str] = []

    cleaned, emails = EMAIL_RE.subn("", text)
    if emails:
        issues.append("email_removed")
    cleaned, urls = URL_RE.subn("", cleaned)
    if urls:
        issues.append("url_removed")
    cleaned, phones = PHONE_RE.subn("", cleaned)
    if phones:
        issues.append("phone_removed")

    if SHAMING_RE.search(cleaned):
        issues.append("shaming_language")

    limit = MAX_WORDS_BY_CLASS.get(school_class, 14)
    for sentence in SENTENCE_RE.findall(cleaned):
        if len(sentence.split()) > limit + 6:
            issues.append("sentence_too_long")
            break

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    return OutputReview(text=cleaned, issues=issues)


class StreamSanitiser:
    """Cleans a token stream on the way to the child.

    Only whole whitespace-delimited tokens are released. Neither a URL nor an
    email address contains whitespace, so this makes it impossible to emit the
    first half of one before the cleaner has seen it.
    """

    def __init__(self) -> None:
        self._buffer = ""
        self.issues: list[str] = []

    def feed(self, chunk: str) -> str:
        self._buffer += chunk
        cut = max(self._buffer.rfind(" "), self._buffer.rfind("\n"))
        if cut == -1:
            return ""
        emit, self._buffer = self._buffer[: cut + 1], self._buffer[cut + 1 :]
        return self._clean(emit)

    def flush(self) -> str:
        emit, self._buffer = self._buffer, ""
        return self._clean(emit)

    def _clean(self, text: str) -> str:
        for pattern, issue in ((EMAIL_RE, "email_removed"), (URL_RE, "url_removed"), (PHONE_RE, "phone_removed")):
            text, hits = pattern.subn("", text)
            if hits and issue not in self.issues:
                self.issues.append(issue)
        return text
