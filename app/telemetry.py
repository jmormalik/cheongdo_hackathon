"""Export only application metrics and explicit spans; never question bodies."""
import os

from opentelemetry import metrics, trace

_configured = False
_meter = metrics.get_meter("farming")
_questions = _meter.create_counter("farming.questions", description="Completed AI requests")
_duration = _meter.create_histogram("farming.question.duration", unit="ms")
_tools = _meter.create_counter("farming.tool.calls")


def configure_telemetry() -> None:
    global _configured
    if _configured or not os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        return
    from azure.monitor.opentelemetry import configure_azure_monitor

    configure_azure_monitor(
        logger_name="app",
        enable_live_metrics=False,
        instrumentation_options={
            name: {"enabled": False}
            for name in ("azure_sdk", "django", "fastapi", "flask", "psycopg2", "requests", "urllib", "urllib3")
        },
    )
    _configured = True


def question_span():
    return trace.get_tracer("farming").start_span("farming.question")


def record_question(outcome: str, duration_ms: int) -> None:
    _questions.add(1, {"outcome": outcome})
    _duration.record(duration_ms, {"outcome": outcome})


def record_tool(stage: str) -> None:
    if stage == "tool_running":
        _tools.add(1, {"tool": "GetCropGuidance"})
