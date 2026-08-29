from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LearnerIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    school_class: int = Field(ge=2, le=4)
    language: Literal["de", "en"] = "de"
    avatar: str = Field(default="fox", max_length=20)

    @field_validator("name")
    @classmethod
    def _first_name_only(cls, value: str) -> str:
        # We only ever want a first name. Trim anything after the first word.
        return value.strip().split()[0][:60]


class LearnerPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    school_class: int | None = Field(default=None, ge=2, le=4)
    language: Literal["de", "en"] | None = None
    avatar: str | None = Field(default=None, max_length=20)


class LearnerOut(BaseModel):
    id: str
    name: str
    school_class: int
    language: str
    avatar: str

    model_config = {"from_attributes": True}


class SessionIn(BaseModel):
    learner_id: str
    subject: Literal["math", "german"] | None = None
    topic_id: str | None = None


class SessionOut(BaseModel):
    id: str
    learner_id: str
    subject: str | None
    topic_id: str | None
    started_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    intercepted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatIn(BaseModel):
    session_id: str
    message: str = Field(min_length=1)


class TopicOut(BaseModel):
    id: str
    subject: str
    label: str
