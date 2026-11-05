"""FastAPI runtime boundary owned by J."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.agent import AgentExecutionError, CropAgent, CropGuidanceAgent
from app.contracts.models import Guidance, QuestionRequest, SCENARIO_ID
from app.contracts.services import GuidanceService, GuidanceUnavailableError
from app.guidance import JsonGuidanceService
from app.contracts.sse import SseEventFactory

logger = logging.getLogger(__name__)
MAX_CONCURRENT_AI_REQUESTS = 2


def create_app(
    *,
    guidance_service: GuidanceService | None = None,
    crop_agent: CropAgent | None = None,
) -> FastAPI:
    service = guidance_service if guidance_service is not None else JsonGuidanceService()
    agent = crop_agent or CropGuidanceAgent()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_AI_REQUESTS)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(title="This Week Farming", lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/guidance")
    async def get_guidance() -> Guidance:
        return await _load_guidance(service)

    @app.post("/api/questions")
    async def ask_question(request: Request, question: QuestionRequest) -> StreamingResponse:
        _validate_scenario(question.scenario_id)
        guidance = await _load_guidance(service)
        _validate_card(question.card_id, guidance)

        if semaphore.locked():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "capacity_exceeded", "message": "잠시 후 다시 시도해 주세요."},
            )

        await semaphore.acquire()
        request_id = str(uuid.uuid4())
        return StreamingResponse(
            _question_events(request, request_id, question, guidance, agent, semaphore),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static-assets")
    app.mount("/", StaticFiles(directory=static_dir, html=True, check_dir=False), name="static")
    return app


async def _load_guidance(service: GuidanceService) -> Guidance:
    try:
        return await service.get_guidance(SCENARIO_ID)
    except GuidanceUnavailableError as error:
        logger.info("guidance unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "guidance_unavailable", "message": "점검 자료를 준비 중입니다."},
        ) from error


def _validate_scenario(scenario_id: str) -> None:
    if scenario_id != SCENARIO_ID:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unsupported_scenario", "message": "지원하지 않는 시나리오입니다."},
        )


def _validate_card(card_id: str | None, guidance: Guidance) -> None:
    if card_id is not None and card_id not in {card.id for card in guidance.cards}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unknown_card", "message": "선택한 점검 항목을 찾을 수 없습니다."},
        )


async def _question_events(
    request: Request,
    request_id: str,
    question: QuestionRequest,
    guidance: Guidance,
    agent: CropAgent,
    semaphore: asyncio.Semaphore,
) -> AsyncIterator[str]:
    events = SseEventFactory(request_id)
    progress: asyncio.Queue[str] = asyncio.Queue()
    started_at = time.monotonic()

    async def report_progress(stage: str) -> None:
        await progress.put(stage)

    task = asyncio.create_task(agent.answer(question, guidance, report_progress))
    try:
        yield events.build("status", {"stage": "validating"})
        while not task.done():
            if await request.is_disconnected():
                task.cancel()
                raise asyncio.CancelledError
            progress_task = asyncio.create_task(progress.get())
            done, pending = await asyncio.wait(
                {task, progress_task},
                timeout=0.25,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for pending_task in pending:
                pending_task.cancel()
            if progress_task in done:
                yield events.build("status", {"stage": progress_task.result()})

        answer = await task
        yield events.build(
            "result",
            {
                "answer": answer.model_dump(mode="json", by_alias=True),
                "sources": [
                    source.model_dump(mode="json", by_alias=True)
                    for source in guidance.sources
                ],
                "dataKind": guidance.data_kind.value,
            },
        )
        outcome = "success"
    except AgentExecutionError as error:
        yield events.build(
            "error",
            {"code": error.code, "message": error.message, "retryable": error.retryable},
        )
        outcome = "error"
    except asyncio.CancelledError:
        task.cancel()
        raise
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        semaphore.release()
        duration_ms = round((time.monotonic() - started_at) * 1_000)
        logger.info(
            "question_completed request_id=%s tool=GetCropGuidance outcome=%s duration_ms=%s",
            request_id,
            locals().get("outcome", "cancelled"),
            duration_ms,
        )

    yield events.build("complete", {"outcome": outcome})


app = create_app()
