from itertools import combinations
from typing import Iterable

from sqlmodel import Session

from app.models.candidate import DuplicateResult, RawCandidate
from app.models.enums import CandidateClass

SIZE_TOLERANCE_RATIO = 0.02
PRICE_TOLERANCE_RATIO = 0.02


def _is_close(a: float | None, b: float | None, tolerance_ratio: float) -> bool:
    if a is None or b is None:
        return False
    denom = max(abs(a), abs(b), 1e-9)
    return abs(a - b) / denom <= tolerance_ratio


def _same_listing(a: RawCandidate, b: RawCandidate) -> tuple[bool, str]:
    if a.source_url and b.source_url and a.source_url.rstrip("/") == b.source_url.rstrip("/"):
        return True, "identical source_url"
    same_area = bool(a.market_area) and a.market_area == b.market_area
    same_land_type = bool(a.land_type) and a.land_type == b.land_type
    close_size = _is_close(a.size_sqm, b.size_sqm, SIZE_TOLERANCE_RATIO)
    close_price = _is_close(a.unit_price, b.unit_price, PRICE_TOLERANCE_RATIO)
    if same_area and same_land_type and close_size and close_price:
        return True, "matching market_area/land_type/size/unit_price within tolerance"
    return False, ""


def detect_duplicates(session: Session, candidates: Iterable[RawCandidate], persist: bool = True) -> list[DuplicateResult]:
    ordered = sorted(candidates, key=lambda c: (c.created_at, c.id or 0))
    duplicates: list[DuplicateResult] = []
    already_flagged: set[int] = set()
    for original, candidate in combinations(ordered, 2):
        if candidate.id in already_flagged:
            continue
        is_dup, reason = _same_listing(original, candidate)
        if not is_dup:
            continue
        candidate.candidate_class = CandidateClass.DUPLICATE
        session.add(candidate)
        record = DuplicateResult(
            raw_candidate_id=candidate.id,
            duplicate_of_id=original.id,
            similarity_score=1.0,
            reason=reason,
        )
        duplicates.append(record)
        already_flagged.add(candidate.id)
        if persist:
            session.add(record)
    if persist and duplicates:
        session.commit()
        for record in duplicates:
            session.refresh(record)
    return duplicates
