"""Load the fixed guidance scenario and validate its evidence references."""

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set
from urllib.parse import urlparse

from pydantic import ValidationError

from app.contracts.models import Guidance
from app.contracts.services import GuidanceService, GuidanceUnavailableError


SCENARIO_ID = "cheongdo-persimmon-postharvest"
DEFAULT_GUIDANCE_PATH = Path(__file__).parent / "data" / "guidance.json"


class GuidanceDataError(ValueError):
    """Raised when guidance data violates the documented data contract."""


def _require_text(value: Any, field: str, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuidanceDataError("{} must be a non-empty string ({})".format(field, context))
    if value != value.strip():
        raise GuidanceDataError("{} must not have surrounding whitespace ({})".format(field, context))
    return value


def _is_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed_date.isoformat() == value


def validate_guidance(guidance: Any) -> None:
    """Validate a Guidance document; raise GuidanceDataError on invalid input."""
    if not isinstance(guidance, dict):
        raise GuidanceDataError("guidance must be a JSON object")

    scenario_id = _require_text(guidance.get("scenarioId"), "scenarioId", "guidance")
    if scenario_id != SCENARIO_ID:
        raise GuidanceDataError("unsupported scenarioId: {}".format(scenario_id))

    data_kind = guidance.get("dataKind")
    if data_kind not in ("reviewed_static", "fixture"):
        raise GuidanceDataError("dataKind must be reviewed_static or fixture")

    reviewed_at = guidance.get("reviewedAt")
    if data_kind == "reviewed_static":
        if not _is_iso_date(reviewed_at):
            raise GuidanceDataError("reviewed_static guidance requires an ISO reviewedAt date")
    elif reviewed_at is not None:
        raise GuidanceDataError("fixture guidance must not claim a reviewedAt date")

    sources = guidance.get("sources")
    cards = guidance.get("cards")
    if not isinstance(sources, list):
        raise GuidanceDataError("sources must be a list")
    if not isinstance(cards, list):
        raise GuidanceDataError("cards must be a list")
    if len(cards) > 3:
        raise GuidanceDataError("guidance may contain at most 3 cards")
    if data_kind == "reviewed_static" and not sources:
        raise GuidanceDataError("reviewed_static guidance requires at least one source")

    source_ids: Set[str] = set()
    for index, source in enumerate(sources):
        context = "sources[{}]".format(index)
        if not isinstance(source, dict):
            raise GuidanceDataError("{} must be an object".format(context))
        source_id = _require_text(source.get("id"), "id", context)
        if source_id in source_ids:
            raise GuidanceDataError("duplicate source id: {}".format(source_id))
        source_ids.add(source_id)

        _require_text(source.get("title"), "title", context)
        _require_text(source.get("scope"), "scope", context)
        published_at = source.get("publishedAt")
        url = source.get("url")
        if data_kind == "fixture":
            if url is not None or published_at is not None:
                raise GuidanceDataError(
                    "{} fixture source records must not claim an external URL or publication date".format(
                        context
                    )
                )
        else:
            url = _require_text(url, "url", context)
            try:
                parsed_url = urlparse(url)
            except ValueError as error:
                raise GuidanceDataError("{} url is malformed".format(context)) from error
            if (
                parsed_url.scheme not in ("http", "https")
                or not parsed_url.hostname
                or parsed_url.username is not None
                or parsed_url.password is not None
            ):
                raise GuidanceDataError("{} url must be an absolute HTTP(S) URL".format(context))
            if published_at is not None and not _is_iso_date(published_at):
                raise GuidanceDataError("{} publishedAt must be an ISO date or null".format(context))

    card_ids: Set[str] = set()
    for index, card in enumerate(cards):
        context = "cards[{}]".format(index)
        if not isinstance(card, dict):
            raise GuidanceDataError("{} must be an object".format(context))
        card_id = _require_text(card.get("id"), "id", context)
        if card_id in card_ids:
            raise GuidanceDataError("duplicate card id: {}".format(card_id))
        card_ids.add(card_id)

        _require_text(card.get("title"), "title", context)
        _require_text(card.get("reason"), "reason", context)
        _require_text(card.get("caution"), "caution", context)
        evidence_ids = card.get("evidenceIds")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            raise GuidanceDataError("{} evidenceIds must be a non-empty list".format(context))

        seen_evidence_ids: Set[str] = set()
        for evidence_id in evidence_ids:
            _require_text(evidence_id, "evidenceId", context)
            if evidence_id in seen_evidence_ids:
                raise GuidanceDataError("{} contains duplicate evidence id {}".format(context, evidence_id))
            seen_evidence_ids.add(evidence_id)

            if evidence_id not in source_ids:
                raise GuidanceDataError(
                    "{} references unregistered source id {}".format(context, evidence_id)
                )


def load_guidance(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and validate the guidance JSON, surfacing file and data errors."""
    guidance_path = Path(path) if path is not None else DEFAULT_GUIDANCE_PATH
    try:
        guidance = json.loads(guidance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GuidanceDataError("unable to load guidance data at {}: {}".format(guidance_path, error)) from error

    validate_guidance(guidance)
    return guidance


def get_crop_guidance(
    scenario_id: str = SCENARIO_ID, path: Optional[Path] = None
) -> Dict[str, Any]:
    """Return the single supported scenario or raise for an unknown scenario."""
    if scenario_id != SCENARIO_ID:
        raise GuidanceDataError("unsupported scenarioId: {}".format(scenario_id))
    return load_guidance(path)


def validate_evidence_ids(
    guidance: Mapping[str, Any], evidence_ids: Any
) -> List[str]:
    """Return validated evidence IDs or raise if any are malformed or unregistered."""
    if not isinstance(guidance, Mapping):
        raise GuidanceDataError("guidance must be an object")
    validate_guidance(dict(guidance))
    if not isinstance(evidence_ids, list):
        raise GuidanceDataError("evidenceIds must be a list")

    allowed_ids = {source["id"] for source in guidance["sources"]}

    checked_ids: List[str] = []
    seen_ids: Set[str] = set()
    for evidence_id in evidence_ids:
        _require_text(evidence_id, "evidenceId", "answer")
        if evidence_id in seen_ids:
            raise GuidanceDataError("duplicate answer evidence id: {}".format(evidence_id))
        if evidence_id not in allowed_ids:
            raise GuidanceDataError("unregistered evidence id: {}".format(evidence_id))
        seen_ids.add(evidence_id)
        checked_ids.append(evidence_id)

    return checked_ids


class JsonGuidanceService(GuidanceService):
    """Adapt the validated JSON file to the runtime's shared Guidance contract."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path

    async def get_guidance(self, scenario_id: str) -> Guidance:
        try:
            data = get_crop_guidance(scenario_id, self._path)
            return Guidance.model_validate(data)
        except (GuidanceDataError, ValidationError) as error:
            raise GuidanceUnavailableError("Guidance data is invalid or unavailable.") from error
