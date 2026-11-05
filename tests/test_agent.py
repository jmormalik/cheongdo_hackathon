from types import SimpleNamespace

import pytest

from app.agent import AgentExecutionError, CropGuidanceAgent, ToolExecutionState


def test_agent_parser_accepts_grounded_answer_with_known_evidence() -> None:
    answer = CropGuidanceAgent._parse_answer(
        SimpleNamespace(text='{"kind":"grounded","text":"설명","evidence_ids":["fixture-1"]}')
    )

    CropGuidanceAgent._validate_evidence(
        answer,
        ToolExecutionState(called=True, evidence_ids={"fixture-1"}),
    )


def test_agent_validator_rejects_unknown_evidence() -> None:
    answer = CropGuidanceAgent._parse_answer(
        SimpleNamespace(text='{"kind":"grounded","text":"설명","evidence_ids":["unknown"]}')
    )

    with pytest.raises(AgentExecutionError, match="확인할 수 없는 근거 ID"):
        CropGuidanceAgent._validate_evidence(
            answer,
            ToolExecutionState(called=True, evidence_ids={"fixture-1"}),
        )


def test_agent_validator_rejects_grounded_answer_without_a_tool_call() -> None:
    answer = CropGuidanceAgent._parse_answer(
        SimpleNamespace(text='{"kind":"grounded","text":"설명","evidence_ids":["fixture-1"]}')
    )

    with pytest.raises(AgentExecutionError, match="자료 조회 없이"):
        CropGuidanceAgent._validate_evidence(answer, ToolExecutionState())
