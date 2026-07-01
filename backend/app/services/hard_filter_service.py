import json

from sqlmodel import Session

from app.config import settings
from app.models.candidate import EligibleCandidate, RawCandidate
from app.models.enums import CandidateClass
from app.models.project import SubjectAsset

SCALE_TOLERANCE_RATIO = 0.5


def estimate_adjustment_ratio(candidate: RawCandidate, subject: SubjectAsset) -> float:
    if not candidate.size_sqm or not subject.size_sqm:
        return 0.0
    return min(abs(candidate.size_sqm - subject.size_sqm) / subject.size_sqm, 1.0)


def evaluate_hard_filter(
    candidate: RawCandidate, subject: SubjectAsset, adjustment_ratio: float | None = None
) -> tuple[bool, list[str], float]:
    flags: list[str] = []
    if candidate.candidate_class == CandidateClass.DUPLICATE:
        flags.append("likely_duplicate")
    if not candidate.market_area or candidate.market_area != subject.market_area:
        flags.append("wrong_market_area")
    if not candidate.land_type or candidate.land_type != subject.land_type:
        flags.append("wrong_land_type_or_segment")
    elif (
        subject.planning_segment
        and candidate.planning_segment
        and candidate.planning_segment != subject.planning_segment
    ):
        flags.append("wrong_land_type_or_segment")
    if not candidate.size_sqm or not subject.size_sqm:
        flags.append("missing_price_or_area")
    elif abs(candidate.size_sqm - subject.size_sqm) / subject.size_sqm > SCALE_TOLERANCE_RATIO:
        flags.append("wrong_scale")
    if candidate.unit_price is None and candidate.asking_price is None:
        flags.append("missing_price_or_area")
    if candidate.source_quality and candidate.source_quality.lower() == "weak":
        flags.append("weak_source")
    if not candidate.source_url and not candidate.raw_text:
        flags.append("weak_source")
    ratio = (
        adjustment_ratio
        if adjustment_ratio is not None
        else estimate_adjustment_ratio(candidate, subject)
    )
    if ratio > settings.max_main_adjustment_ratio:
        flags.append("expected_adjustment_over_40pct")
    return len(flags) == 0, flags, ratio


def build_eligible_record(
    candidate: RawCandidate, subject: SubjectAsset, adjustment_ratio: float | None = None
) -> tuple[EligibleCandidate, float]:
    passed, flags, ratio = evaluate_hard_filter(candidate, subject, adjustment_ratio)
    record = EligibleCandidate(
        raw_candidate_id=candidate.id, passed_hard_filter=passed, flags_json=json.dumps(flags)
    )
    if not passed:
        candidate.candidate_class = CandidateClass.REJECT
    return record, ratio


def run_hard_filter(
    session: Session, candidates: list[RawCandidate], subject: SubjectAsset
) -> list[EligibleCandidate]:
    results: list[EligibleCandidate] = []
    for candidate in candidates:
        if candidate.candidate_class == CandidateClass.DUPLICATE:
            continue
        record, _ratio = build_eligible_record(candidate, subject)
        session.add(record)
        session.add(candidate)
        results.append(record)
    session.commit()
    for record in results:
        session.refresh(record)
    return results
