import json
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlmodel import Session, select

from app.models.candidate import ExtractionResult, RawCandidate
from app.models.enums import CandidateClass
from app.services.llm_client import FreeLLMAPIClient, GatewayUnavailableError

EXTRACTION_SYSTEM_PROMPT = (
    "You are a structured data extraction assistant for ValCo TSSS evidence. "
    "Only extract, normalize, classify, and draft a short audit note. "
    "Never invent missing fields, estimate final value, or select final TSSS. "
    "Return null when a field is not present. Respond with one JSON object."
)


class ExtractedFieldsSchema(BaseModel):
    market_area: str | None = None
    land_type: str | None = None
    planning_segment: str | None = None
    size_sqm: float | None = None
    unit_price: float | None = None
    draft_note: str | None = None


def _build_messages(candidate: RawCandidate) -> list[dict[str, str]]:
    raw_payload = {
        "source_url": candidate.source_url,
        "raw_text": candidate.raw_text,
        "market_area": candidate.market_area,
        "land_type": candidate.land_type,
        "planning_segment": candidate.planning_segment,
        "size_sqm": candidate.size_sqm,
        "unit_price": candidate.unit_price,
        "asking_price": candidate.asking_price,
    }
    user_content = (
        "Extract/normalize this raw candidate evidence into schema: "
        "market_area, land_type, planning_segment, size_sqm, "
        "unit_price, draft_note. Raw evidence JSON:\n"
        f"{json.dumps(raw_payload, default=str)}"
    )
    return [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _parse_gateway_response(response: dict[str, Any]) -> ExtractedFieldsSchema:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected gateway response shape: {exc}") from exc

    parsed = json.loads(content) if isinstance(content, str) else content
    return ExtractedFieldsSchema.model_validate(parsed)


def _fallback_from_raw(candidate: RawCandidate) -> ExtractedFieldsSchema:
    return ExtractedFieldsSchema(
        market_area=candidate.market_area,
        land_type=candidate.land_type,
        planning_segment=candidate.planning_segment,
        size_sqm=candidate.size_sqm,
        unit_price=candidate.unit_price,
        draft_note=None,
    )


async def extract_candidate(
    session: Session,
    candidate: RawCandidate,
    client: FreeLLMAPIClient | None = None,
) -> ExtractionResult:
    gateway = client or FreeLLMAPIClient()
    status = "completed"

    try:
        response = await gateway.chat_completion(
            _build_messages(candidate),
            response_format_json=True,
        )
        fields = _parse_gateway_response(response)
    except (GatewayUnavailableError, ValueError, ValidationError):
        fields = _fallback_from_raw(candidate)
        status = "stub_fallback"

    result = ExtractionResult(
        raw_candidate_id=candidate.id,
        extracted_fields_json=fields.model_dump_json(),
        normalized_market_area=fields.market_area,
        normalized_land_type=fields.land_type,
        normalized_planning_segment=fields.planning_segment,
        normalized_size_sqm=fields.size_sqm,
        normalized_unit_price=fields.unit_price,
        draft_note=fields.draft_note,
        extraction_status=status,
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


async def run_extraction_for_project(
    session: Session,
    project_id: int,
    client: FreeLLMAPIClient | None = None,
) -> list[ExtractionResult]:
    statement = select(RawCandidate).where(RawCandidate.project_id == project_id)
    candidates = [
        candidate
        for candidate in session.exec(statement).all()
        if candidate.candidate_class != CandidateClass.DUPLICATE
    ]

    gateway = client or FreeLLMAPIClient()
    results: list[ExtractionResult] = []
    for candidate in candidates:
        results.append(await extract_candidate(session, candidate, client=gateway))
    return results
