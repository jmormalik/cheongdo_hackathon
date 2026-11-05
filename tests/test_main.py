from fastapi.testclient import TestClient

from app.agent import ProgressCallback
from app.contracts.models import Answer, AnswerKind, Card, DataKind, Guidance, QuestionRequest, Source
from app.contracts.services import GuidanceService
from app.main import create_app


class FakeGuidanceService(GuidanceService):
    async def get_guidance(self, scenario_id: str) -> Guidance:
        return Guidance(
            scenario_id=scenario_id,
            data_kind=DataKind.FIXTURE,
            sources=[
                Source(
                    id="fixture-1",
                    title="예시 근거",
                    scope="데모 전용",
                )
            ],
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


class FakeCropAgent:
    async def answer(
        self,
        request: QuestionRequest,
        guidance: Guidance,
        progress: ProgressCallback,
    ) -> Answer:
        await progress("agent_running")
        await progress("tool_running")
        await progress("tool_done")
        return Answer(
            kind=AnswerKind.GROUNDED,
            text="예시 근거에 따른 설명입니다.",
            evidence_ids=["fixture-1"],
        )


def test_healthz_is_available_without_guidance_data() -> None:
    response = TestClient(create_app()).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_guidance_returns_server_owned_scenario() -> None:
    response = TestClient(create_app(guidance_service=FakeGuidanceService())).get("/api/guidance")

    assert response.status_code == 200
    assert response.json()["scenario_id"] == "cheongdo-persimmon-postharvest"
    assert len(response.json()["cards"]) == 1


def test_question_rejects_an_unsupported_scenario_before_agent_execution() -> None:
    response = TestClient(create_app(guidance_service=FakeGuidanceService())).post(
        "/api/questions",
        json={"scenario_id": "other", "question": "왜 점검하나요?"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unsupported_scenario"


def test_question_streams_only_the_validated_final_answer() -> None:
    response = TestClient(
        create_app(guidance_service=FakeGuidanceService(), crop_agent=FakeCropAgent())
    ).post(
        "/api/questions",
        json={
            "scenario_id": "cheongdo-persimmon-postharvest",
            "card_id": "card-1",
            "question": "왜 점검하나요?",
        },
    )

    assert response.status_code == 200
    assert "event: result" in response.text
    assert '"evidence_ids": ["fixture-1"]' in response.text
    assert "event: complete" in response.text
