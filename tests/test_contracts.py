from app.contracts.models import Answer, AnswerKind
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
