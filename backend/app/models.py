import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Parent(Base):
    """The adult who owns the account. Children never sign up themselves."""

    __tablename__ = "parents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    learners: Mapped[list["Learner"]] = relationship(back_populates="parent", cascade="all, delete-orphan")


class Learner(Base):
    """One child. Every row in every other table hangs off one of these."""

    __tablename__ = "learners"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    parent_id: Mapped[str] = mapped_column(ForeignKey("parents.id", ondelete="CASCADE"), index=True)
    # First name only. We never ask a child for a surname.
    name: Mapped[str] = mapped_column(String(60))
    school_class: Mapped[int] = mapped_column(Integer)  # 2, 3 or 4
    language: Mapped[str] = mapped_column(String(2), default="de")  # "de" | "en"
    avatar: Mapped[str] = mapped_column(String(20), default="fox")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    parent: Mapped[Parent] = relationship(back_populates="learners")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "math" | "german"
    topic_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(12))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    # True when the guardrail layer answered instead of the model.
    intercepted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (Index("ix_messages_session_created", "session_id", "created_at"),)


class Exercise(Base):
    """A single generated item. Phase 2 fills these; the table exists from the start."""

    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    # One worksheet's worth of tasks share a sheet_id.
    sheet_id: Mapped[str] = mapped_column(String(32), index=True)
    subject: Mapped[str] = mapped_column(String(20))
    topic_id: Mapped[str] = mapped_column(String(60), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    kind: Mapped[str] = mapped_column(String(20), default="arith")
    position: Mapped[int] = mapped_column(Integer, default=0)
    prompt: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    # [{"id": "a", "answer": "240", "label": "60 · 4"}, ...]
    blanks: Mapped[list] = mapped_column(JSON, default=list)
    accepted_variants: Mapped[list] = mapped_column(JSON, default=list)
    hints: Mapped[list] = mapped_column(JSON, default=list)
    # How many hints the child has been given. The ladder is enforced from this
    # number, not from the model's willingness to hold back.
    hint_level: Mapped[int] = mapped_column(Integer, default=0)
    solved: Mapped[bool] = mapped_column(Boolean, default=False)
    # "python" when generated deterministically, otherwise "<provider>:<model>".
    source: Mapped[str] = mapped_column(String(60), default="python")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    blank_id: Mapped[str] = mapped_column(String(8), default="a")
    given: Mapped[str] = mapped_column(Text)
    correct: Mapped[bool] = mapped_column(Boolean)
    # How we decided: "exact" | "normalised" | "judge"
    graded_by: Mapped[str] = mapped_column(String(20), default="exact")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class TopicMastery(Base):
    __tablename__ = "topic_mastery"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[str] = mapped_column(String(60))
    score: Mapped[float] = mapped_column(Float, default=0.0)  # rolling 0..1
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (UniqueConstraint("learner_id", "topic_id", name="uq_mastery_learner_topic"),)


class SafetyFlag(Base):
    """Written whenever guardrails intercept. Surfaced to the parent in phase 3."""

    __tablename__ = "safety_flags"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str] = mapped_column(String(30))
    excerpt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class LLMCall(Base):
    """Per-call telemetry. Feeds cost reporting and the router's speed policy."""

    __tablename__ = "llm_calls"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    learner_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    task: Mapped[str] = mapped_column(String(40))
    tier: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(60))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
