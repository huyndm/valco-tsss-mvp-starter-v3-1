from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.enums import CandidateClass


class RawCandidate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    source_url: str | None = None
    raw_text: str | None = None
    market_area: str | None = None
    land_type: str | None = None
    planning_segment: str | None = None
    size_sqm: float | None = None
    unit_price: float | None = None
    asking_price: float | None = None
    source_quality: str | None = None
    evidence_timestamp: datetime | None = None
    candidate_class: CandidateClass = Field(default=CandidateClass.RAW_CANDIDATE)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DuplicateResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    raw_candidate_id: int = Field(foreign_key="rawcandidate.id")
    duplicate_of_id: int | None = Field(default=None, foreign_key="rawcandidate.id")
    similarity_score: float
    reason: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractionResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    raw_candidate_id: int = Field(foreign_key="rawcandidate.id")
    extracted_fields_json: str | None = None
    normalized_market_area: str | None = None
    normalized_land_type: str | None = None
    normalized_planning_segment: str | None = None
    normalized_size_sqm: float | None = None
    normalized_unit_price: float | None = None
    extraction_status: str = Field(default="stub_pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EligibleCandidate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    raw_candidate_id: int = Field(foreign_key="rawcandidate.id")
    passed_hard_filter: bool
    flags_json: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScoringResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    eligible_candidate_id: int = Field(foreign_key="eligiblecandidate.id")
    market_area_score: float = 0.0
    land_type_score: float = 0.0
    size_score: float = 0.0
    unit_price_score: float = 0.0
    source_link_score: float = 0.0
    adjustment_ratio_score: float = 0.0
    adjustment_ratio: float = 0.0
    total_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Top10Recommendation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    eligible_candidate_id: int = Field(foreign_key="eligiblecandidate.id")
    rank: int
    candidate_class: CandidateClass = Field(default=CandidateClass.RECOMMENDED_TOP_10)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Final3Selection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    eligible_candidate_id: int = Field(foreign_key="eligiblecandidate.id")
    selected_by: str
    is_override: bool = Field(default=False)
    override_reason: str | None = None
    candidate_class: CandidateClass = Field(default=CandidateClass.MAIN_SELECTED_3)
    created_at: datetime = Field(default_factory=datetime.utcnow)
