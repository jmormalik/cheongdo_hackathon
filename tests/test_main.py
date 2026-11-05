from fastapi.testclient import TestClient
import asyncio

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


class FixtureCropAgent:
    async def answer(
        self,
        request: QuestionRequest,
        guidance: Guidance,
        progress: ProgressCallback,
    ) -> Answer:
        await progress("tool_running")
        await progress("tool_done")
        return Answer(
            kind=AnswerKind.GROUNDED,
            text="데모 fixture를 사용한 설명입니다.",
            evidence_ids=[guidance.cards[0].evidence_ids[0]],
        )


def test_healthz_is_available_without_guidance_data() -> None:
    response = TestClient(create_app()).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_ui_and_module_assets_are_served() -> None:
    client = TestClient(create_app())
    for path in ("/", "/demo", "/static/styles.css", "/static/app.js", "/static/sse.mjs", "/static/contracts.mjs"):
        assert client.get(path).status_code == 200, path


def test_delayed_agent_survives_progress_and_polling() -> None:
    class DelayedAgent(FixtureCropAgent):
        async def answer(self, request, guidance, progress):
            await progress("tool_running")
            await asyncio.sleep(0.4)
            return await super().answer(request, guidance, progress)

    response = TestClient(create_app(crop_agent=DelayedAgent())).post(
        "/api/questions", json={"scenarioId": "cheongdo-persimmon-postharvest", "question": "점검 이유"}
    )
    assert "event: result" in response.text
    assert '"outcome": "success"' in response.text
    assert "event: complete" in response.text


def test_guidance_returns_server_owned_scenario() -> None:
    response = TestClient(create_app(guidance_service=FakeGuidanceService())).get("/api/guidance")

    assert response.status_code == 200
    assert response.json()["scenarioId"] == "cheongdo-persimmon-postharvest"
    assert len(response.json()["cards"]) == 1


def test_default_guidance_service_returns_fixture_data() -> None:
    response = TestClient(create_app()).get("/api/guidance")

    assert response.status_code == 200
    data = response.json()
    assert data["dataKind"] == "fixture"
    assert data["sources"][0]["url"] is None
    assert data["cards"][0]["evidenceIds"] == [data["sources"][0]["id"]]


def test_default_guidance_completes_fixture_question_in_ui_wire_format() -> None:
    response = TestClient(create_app(crop_agent=FixtureCropAgent())).post(
        "/api/questions",
        json={
            "scenarioId": "cheongdo-persimmon-postharvest",
            "cardId": "fixture-card-01",
            "question": "이 예시가 실제 권고인가요?",
        },
    )

    assert response.status_code == 200
    assert '"evidenceIds": ["fixture-evidence-01"]' in response.text
    assert '"dataKind": "fixture"' in response.text
    assert '"url": null' in response.text
    assert "event: complete" in response.text


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
    assert '"evidenceIds": ["fixture-1"]' in response.text
    assert "event: complete" in response.text
