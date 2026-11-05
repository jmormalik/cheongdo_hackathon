"""Pydantic models shared by the API, agent, data adapter, and UI."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


SCENARIO_ID = "cheongdo-persimmon-postharvest"


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.title() for part in rest)


class ContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class DataKind(StrEnum):
    REVIEWED_STATIC = "reviewed_static"
    FIXTURE = "fixture"


class Source(ContractModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    url: str | None = None
    published_at: str | None = None
    reviewed_at: str | None = None
    scope: str = Field(min_length=1, max_length=500)
    usage_terms: str | None = None
    display_text: str | None = None


class Card(ContractModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2_000)
    caution: str = Field(min_length=1, max_length=2_000)
    evidence_ids: list[str] = Field(min_length=1, max_length=10)


class Guidance(ContractModel):
    scenario_id: str = SCENARIO_ID
    data_kind: DataKind
    reviewed_at: str | None = None
    sources: list[Source] = Field(max_length=20)
    cards: list[Card] = Field(max_length=3)


class QuestionRequest(ContractModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=None,
        populate_by_name=True,
        str_strip_whitespace=True,
    )
    scenario_id: str = Field(min_length=1, max_length=100)
    card_id: str | None = Field(default=None, max_length=100)
    question: str = Field(min_length=1, max_length=500)

    @model_validator(mode="before")
    @classmethod
    def accept_wire_field_names(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        for wire_name, field_name in (
            ("scenarioId", "scenario_id"),
            ("cardId", "card_id"),
        ):
            if wire_name in normalized:
                if field_name in normalized:
                    raise ValueError("{} and {} cannot both be provided".format(wire_name, field_name))
                normalized[field_name] = normalized.pop(wire_name)
        return normalized


class AnswerKind(StrEnum):
    GROUNDED = "grounded"
    OUT_OF_SCOPE = "out_of_scope"


class Answer(ContractModel):
    kind: AnswerKind
    text: str = Field(min_length=1, max_length=4_000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=10)
