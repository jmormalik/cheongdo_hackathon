"""Pydantic models shared by the API, agent, data adapter, and UI."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


SCENARIO_ID = "cheongdo-persimmon-postharvest"


class DataKind(StrEnum):
    REVIEWED_STATIC = "reviewed_static"
    FIXTURE = "fixture"


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    url: str | None = None
    published_at: str | None = None
    reviewed_at: str | None = None
    scope: str = Field(min_length=1, max_length=500)
    usage_terms: str | None = None
    display_text: str | None = None


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2_000)
    caution: str = Field(min_length=1, max_length=2_000)
    evidence_ids: list[str] = Field(min_length=1, max_length=10)


class Guidance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = SCENARIO_ID
    data_kind: DataKind
    reviewed_at: str | None = None
    sources: list[Source] = Field(max_length=20)
    cards: list[Card] = Field(max_length=3)


class QuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scenario_id: str = Field(min_length=1, max_length=100)
    card_id: str | None = Field(default=None, max_length=100)
    question: str = Field(min_length=1, max_length=500)


class AnswerKind(StrEnum):
    GROUNDED = "grounded"
    OUT_OF_SCOPE = "out_of_scope"


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: AnswerKind
    text: str = Field(min_length=1, max_length=4_000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=10)
