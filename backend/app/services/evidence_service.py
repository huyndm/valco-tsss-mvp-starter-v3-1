from datetime import datetime

from sqlmodel import Session, select

from app.config import settings
from app.models.candidate import RawCandidate
from app.models.enums import CandidateClass


class RawPoolLimitExceeded(Exception):
    pass


def count_raw_candidates(session: Session, project_id: int) -> int:
    return len(session.exec(select(RawCandidate).where(RawCandidate.project_id == project_id)).all())


def add_raw_candidate(
    session: Session,
    project_id: int,
    source_url: str | None = None,
    raw_text: str | None = None,
    market_area: str | None = None,
    land_type: str | None = None,
    planning_segment: str | None = None,
    size_sqm: float | None = None,
    unit_price: float | None = None,
    asking_price: float | None = None,
    source_quality: str | None = None,
    evidence_timestamp: datetime | None = None,
) -> RawCandidate:
    if count_raw_candidates(session, project_id) >= settings.max_raw_candidates:
        raise RawPoolLimitExceeded(f"Raw candidate pool cap reached: {settings.max_raw_candidates}")
    candidate = RawCandidate(
        project_id=project_id,
        source_url=source_url,
        raw_text=raw_text,
        market_area=market_area,
        land_type=land_type,
        planning_segment=planning_segment,
        size_sqm=size_sqm,
        unit_price=unit_price,
        asking_price=asking_price,
        source_quality=source_quality,
        evidence_timestamp=evidence_timestamp or datetime.utcnow(),
        candidate_class=CandidateClass.RAW_CANDIDATE,
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def list_raw_candidates(session: Session, project_id: int) -> list[RawCandidate]:
    return list(session.exec(select(RawCandidate).where(RawCandidate.project_id == project_id)).all())
