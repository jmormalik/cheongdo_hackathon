from types import SimpleNamespace

import pytest

from app.agent import AgentExecutionError, CropGuidanceAgent
from app.contracts.models import Card, DataKind, Guidance, Source


def _guidance() -> Guidance:
    return Guidance(
        data_kind=DataKind.FIXTURE,
        sources=[Source(id="fixture-1", title="예시 근거", scope="데모 전용")],
        cards=[
            Card(
                id="card-1",
                title="점검",
                reason="예시 이유",
                caution="예시 주의",
                evidence_ids=["fixture-1"],
            )
        ],
    )


def test_agent_parser_accepts_grounded_answer_with_known_evidence() -> None:
    answer = CropGuidanceAgent._parse_answer(
        SimpleNamespace(text='{"kind":"grounded","text":"설명","evidence_ids":["fixture-1"]}')
    )

    CropGuidanceAgent._validate_evidence(answer, _guidance())


def test_agent_validator_rejects_unknown_evidence() -> None:
    answer = CropGuidanceAgent._parse_answer(
        SimpleNamespace(text='{"kind":"grounded","text":"설명","evidence_ids":["unknown"]}')
    )

    with pytest.raises(AgentExecutionError, match="확인할 수 없는 근거 ID"):
        CropGuidanceAgent._validate_evidence(answer, _guidance())
