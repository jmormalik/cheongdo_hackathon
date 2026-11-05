from app.contracts.models import Answer, AnswerKind, QuestionRequest, SCENARIO_ID
from app.contracts.sse import SseEventFactory


def test_sse_events_increment_sequence_numbers() -> None:
    events = SseEventFactory("request-1")

    first = events.build("status", {"stage": "validating"})
    second = events.build("complete", {"outcome": "success"})

    assert '"seq": 1' in first
    assert '"seq": 2' in second
    assert "event: status" in first
    assert "event: complete" in second


def test_out_of_scope_answer_can_omit_evidence() -> None:
    answer = Answer(kind=AnswerKind.OUT_OF_SCOPE, text="이 앱의 점검 범위 안에서 질문해 주세요.")

    assert answer.evidence_ids == []


def test_question_request_accepts_ui_camel_case_fields() -> None:
    request = QuestionRequest.model_validate(
        {
            "scenarioId": SCENARIO_ID,
            "cardId": "fixture-card-01",
            "question": " 왜 점검하나요? ",
        }
    )

    assert request.scenario_id == SCENARIO_ID
    assert request.card_id == "fixture-card-01"
    assert request.question == "왜 점검하나요?"
