from types import SimpleNamespace

import pytest

from app.agent import (
    MAX_TOOL_CALLS,
    OUT_OF_SCOPE_MESSAGE,
    AgentExecutionError,
    CropGuidanceAgent,
    ToolExecutionState,
)
from app.contracts.models import Answer, AnswerKind


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


def test_tool_execution_state_rejects_a_fourth_tool_call() -> None:
    state = ToolExecutionState()

    for _ in range(MAX_TOOL_CALLS):
        state.record_call()

    with pytest.raises(AgentExecutionError, match="조회 횟수가 제한을 초과"):
        state.record_call()

    assert state.call_count == MAX_TOOL_CALLS
    assert state.limit_exceeded is True


def test_agent_normalizes_out_of_scope_answer_text() -> None:
    answer = Answer(
        kind=AnswerKind.OUT_OF_SCOPE,
        text="농약을 10배 희석해 사용하세요.",
    )

    normalized = CropGuidanceAgent._normalize_answer(answer)

    assert normalized.text == OUT_OF_SCOPE_MESSAGE
    assert normalized.evidence_ids == []
