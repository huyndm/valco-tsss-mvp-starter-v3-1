import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models.audit import AuditLog
from app.models.candidate import (
    DuplicateResult,
    EligibleCandidate,
    ExtractionResult,
    Final3Selection,
    RawCandidate,
    ScoringResult,
    Top10Recommendation,
)
from app.models.enums import CandidateClass
from app.models.project import Project, SubjectAsset

# Phase 3.4 — TSSS Brain + OmniRoute
from app.services import (
    dedup_service,
    export_service,
    hard_filter_service,
    scoring_service,
    selection_service,
    tsss_brain_service,
)
from app.services.evidence_service import (
    RawPoolLimitExceeded,
    add_raw_candidate,
    list_raw_candidates,
)
from app.services.extraction_service import run_extraction_for_project
from app.services.llm_client import FreeLLMAPIClient

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


# Pydantic Schemas for Requests
class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class SubjectAssetCreate(BaseModel):
    address: str
    market_area: str
    land_type: str
    planning_segment: str | None = None
    size_sqm: float


class RawCandidateCreate(BaseModel):
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


class Final3SelectionCreate(BaseModel):
    eligible_candidate_ids: list[int]
    selected_by: str
    override_reason: str | None = None


# Phase 3.4 — TSSS Brain request schemas
class TsssBrainExtractCandidateRequest(BaseModel):
    source_url: str | None = None
    raw_text: str
    create_raw_candidate: bool = False


# Core pipeline routes
@router.get("/tsss/pipeline")
def tsss_pipeline():
    return {
        "pipeline": [
            "raw candidate search up to 1,000",
            "deduplicate",
            "FreeLLMAPI extraction/normalization",
            "hard filter",
            "eligible pool",
            "Top 10 recommended",
            "analyst/user final 3",
            "export/audit",
        ]
    }


# Project Routes
@router.post("/projects")
def create_project(project_data: ProjectCreate, session: SessionDep):
    db_project = Project(name=project_data.name, description=project_data.description)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project


@router.get("/projects")
def get_projects(session: SessionDep):
    return session.exec(select(Project)).all()


@router.get("/projects/{project_id}")
def get_project(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# Subject Asset Routes
@router.post("/projects/{project_id}/subject-asset")
def create_subject_asset(project_id: int, asset_data: SubjectAssetCreate, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = session.exec(
        select(SubjectAsset).where(SubjectAsset.project_id == project_id)
    ).first()
    if existing:
        existing.address = asset_data.address
        existing.market_area = asset_data.market_area
        existing.land_type = asset_data.land_type
        existing.planning_segment = asset_data.planning_segment
        existing.size_sqm = asset_data.size_sqm
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        new_asset = SubjectAsset(
            project_id=project_id,
            address=asset_data.address,
            market_area=asset_data.market_area,
            land_type=asset_data.land_type,
            planning_segment=asset_data.planning_segment,
            size_sqm=asset_data.size_sqm,
        )
        session.add(new_asset)
        session.commit()
        session.refresh(new_asset)
        return new_asset


@router.get("/projects/{project_id}/subject-asset")
def get_subject_asset(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    asset = session.exec(select(SubjectAsset).where(SubjectAsset.project_id == project_id)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Subject asset not found")
    return asset


# Raw Candidate Routes
@router.post("/projects/{project_id}/raw-candidates")
def create_raw_candidates(
    project_id: int,
    candidates: list[RawCandidateCreate] | RawCandidateCreate,
    session: SessionDep,
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if isinstance(candidates, list):
        created = []
        for c in candidates:
            try:
                candidate_obj = add_raw_candidate(
                    session,
                    project_id=project_id,
                    source_url=c.source_url,
                    raw_text=c.raw_text,
                    market_area=c.market_area,
                    land_type=c.land_type,
                    planning_segment=c.planning_segment,
                    size_sqm=c.size_sqm,
                    unit_price=c.unit_price,
                    asking_price=c.asking_price,
                    source_quality=c.source_quality,
                    evidence_timestamp=c.evidence_timestamp,
                )
                created.append(candidate_obj)
            except RawPoolLimitExceeded as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
        for c in created:
            session.refresh(c)
        return created
    else:
        try:
            candidate_obj = add_raw_candidate(
                session,
                project_id=project_id,
                source_url=candidates.source_url,
                raw_text=candidates.raw_text,
                market_area=candidates.market_area,
                land_type=candidates.land_type,
                planning_segment=candidates.planning_segment,
                size_sqm=candidates.size_sqm,
                unit_price=candidates.unit_price,
                asking_price=candidates.asking_price,
                source_quality=candidates.source_quality,
                evidence_timestamp=candidates.evidence_timestamp,
            )
            return candidate_obj
        except RawPoolLimitExceeded as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/projects/{project_id}/raw-candidates")
def get_raw_candidates(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    candidates = list_raw_candidates(session, project_id)
    result = []
    for c in candidates:
        # Build enriched candidate dict with dedup and hard filter status
        c_dict = {
            "id": c.id,
            "project_id": c.project_id,
            "source_url": c.source_url,
            "raw_text": c.raw_text,
            "market_area": c.market_area,
            "land_type": c.land_type,
            "planning_segment": c.planning_segment,
            "size_sqm": c.size_sqm,
            "unit_price": c.unit_price,
            "asking_price": c.asking_price,
            "source_quality": c.source_quality,
            "evidence_timestamp": c.evidence_timestamp.isoformat()
            if c.evidence_timestamp
            else None,
            "candidate_class": c.candidate_class.value
            if hasattr(c.candidate_class, "value")
            else str(c.candidate_class),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "dedup_status": None,
            "hard_filter_status": None,
            "hard_filter_flags": [],
            "adjustment_warnings": [],
        }

        # Determine dedup status from DuplicateResult table and candidate_class
        dup = session.exec(
            select(DuplicateResult).where(DuplicateResult.raw_candidate_id == c.id)
        ).first()
        if dup:
            c_dict["dedup_status"] = f"duplicate_of_{dup.duplicate_of_id}"
        elif c.candidate_class == CandidateClass.DUPLICATE:
            c_dict["dedup_status"] = "flagged_duplicate"
        else:
            c_dict["dedup_status"] = "unique"

        # Determine hard filter status from EligibleCandidate table
        el = session.exec(
            select(EligibleCandidate).where(EligibleCandidate.raw_candidate_id == c.id)
        ).first()
        if el:
            c_dict["hard_filter_status"] = "passed" if el.passed_hard_filter else "rejected"
            if el.flags_json:
                flags = json.loads(el.flags_json)
                c_dict["hard_filter_flags"] = flags
                c_dict["adjustment_warnings"] = [
                    f
                    for f in flags
                    if "adjustment" in f.lower()
                    or "40" in f
                    or "land_type" in f.lower()
                    or "missing" in f.lower()
                ]
        elif c.candidate_class == CandidateClass.REJECT:
            c_dict["hard_filter_status"] = "rejected"
        else:
            c_dict["hard_filter_status"] = "pending"

        result.append(c_dict)
    return result


# Extraction Routes
@router.post("/extraction/run/{project_id}")
async def run_extraction(project_id: int, session: SessionDep):
    existing = session.exec(
        select(RawCandidate).where(RawCandidate.project_id == project_id)
    ).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="No raw candidates found for project")

    results = await run_extraction_for_project(session, project_id)
    return {
        "project_id": project_id,
        "extracted_count": len(results),
        "results": [
            {
                "id": result.id,
                "raw_candidate_id": result.raw_candidate_id,
                "extraction_status": result.extraction_status,
            }
            for result in results
        ],
    }


@router.get("/extraction/{project_id}")
def get_extraction_results(project_id: int, session: SessionDep):
    raw_ids = [
        candidate.id
        for candidate in session.exec(
            select(RawCandidate).where(RawCandidate.project_id == project_id)
        ).all()
    ]

    if not raw_ids:
        return {"project_id": project_id, "results": []}

    results = session.exec(
        select(ExtractionResult).where(ExtractionResult.raw_candidate_id.in_(raw_ids))
    ).all()
    return {
        "project_id": project_id,
        "results": [
            {
                "id": result.id,
                "raw_candidate_id": result.raw_candidate_id,
                "normalized_market_area": result.normalized_market_area,
                "normalized_land_type": result.normalized_land_type,
                "normalized_planning_segment": result.normalized_planning_segment,
                "normalized_size_sqm": result.normalized_size_sqm,
                "normalized_unit_price": result.normalized_unit_price,
                "extraction_status": result.extraction_status,
                "draft_note": result.draft_note,
            }
            for result in results
        ],
    }


# Deduplication Run Route
@router.post("/dedup/run/{project_id}")
def run_dedup(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    candidates = session.exec(
        select(RawCandidate).where(RawCandidate.project_id == project_id)
    ).all()
    for c in candidates:
        if (
            c.candidate_class == CandidateClass.DUPLICATE
            or c.candidate_class == CandidateClass.REJECT
        ):
            c.candidate_class = CandidateClass.RAW_CANDIDATE
            session.add(c)

    cand_ids = [c.id for c in candidates]
    if cand_ids:
        existing_dups = session.exec(
            select(DuplicateResult).where(DuplicateResult.raw_candidate_id.in_(cand_ids))
        ).all()
        for d in existing_dups:
            session.delete(d)
    session.commit()

    candidates = session.exec(
        select(RawCandidate).where(RawCandidate.project_id == project_id)
    ).all()
    duplicates = dedup_service.detect_duplicates(session, candidates)
    return {
        "project_id": project_id,
        "duplicate_count": len(duplicates),
        "duplicates": [
            {
                "raw_candidate_id": d.raw_candidate_id,
                "duplicate_of_id": d.duplicate_of_id,
                "reason": d.reason,
            }
            for d in duplicates
        ],
    }


# Hard Filter Run Route
@router.post("/hard-filter/run/{project_id}")
def run_hard_filter_route(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    subject = session.exec(
        select(SubjectAsset).where(SubjectAsset.project_id == project_id)
    ).first()
    if not subject:
        raise HTTPException(status_code=400, detail="Subject asset not found for project")

    candidates = session.exec(
        select(RawCandidate).where(RawCandidate.project_id == project_id)
    ).all()

    cand_ids = [c.id for c in candidates]
    if cand_ids:
        selections = session.exec(
            select(Final3Selection).where(Final3Selection.project_id == project_id)
        ).all()
        for sel in selections:
            session.delete(sel)
        top10s = session.exec(
            select(Top10Recommendation).where(Top10Recommendation.project_id == project_id)
        ).all()
        for t in top10s:
            session.delete(t)
        eligibles = session.exec(
            select(EligibleCandidate).where(EligibleCandidate.raw_candidate_id.in_(cand_ids))
        ).all()
        elig_ids = [el.id for el in eligibles]
        if elig_ids:
            scorings = session.exec(
                select(ScoringResult).where(ScoringResult.eligible_candidate_id.in_(elig_ids))
            ).all()
            for sc in scorings:
                session.delete(sc)
        for el in eligibles:
            session.delete(el)

    for c in candidates:
        if c.candidate_class != CandidateClass.DUPLICATE:
            c.candidate_class = CandidateClass.RAW_CANDIDATE
            session.add(c)

    session.commit()

    candidates = session.exec(
        select(RawCandidate).where(RawCandidate.project_id == project_id)
    ).all()

    overlaid_data = []
    for candidate in candidates:
        ext = session.exec(
            select(ExtractionResult).where(ExtractionResult.raw_candidate_id == candidate.id)
        ).first()
        if ext:
            orig = {
                "market_area": candidate.market_area,
                "land_type": candidate.land_type,
                "planning_segment": candidate.planning_segment,
                "size_sqm": candidate.size_sqm,
                "unit_price": candidate.unit_price,
            }
            candidate.market_area = ext.normalized_market_area
            candidate.land_type = ext.normalized_land_type
            candidate.planning_segment = ext.normalized_planning_segment
            candidate.size_sqm = ext.normalized_size_sqm
            candidate.unit_price = ext.normalized_unit_price
            overlaid_data.append((candidate, orig))

    results = hard_filter_service.run_hard_filter(session, candidates, subject)

    for candidate, orig in overlaid_data:
        candidate.market_area = orig["market_area"]
        candidate.land_type = orig["land_type"]
        candidate.planning_segment = orig["planning_segment"]
        candidate.size_sqm = orig["size_sqm"]
        candidate.unit_price = orig["unit_price"]
        session.add(candidate)

    session.commit()

    for r in results:
        session.refresh(r)

    return {
        "project_id": project_id,
        "total_evaluated": len(results),
        "passed_count": len([r for r in results if r.passed_hard_filter]),
        "results": [
            {
                "eligible_candidate_id": r.id,
                "raw_candidate_id": r.raw_candidate_id,
                "passed": r.passed_hard_filter,
                "flags": json.loads(r.flags_json) if r.flags_json else [],
            }
            for r in results
        ],
    }


# Scoring and Ranking Run Route
@router.post("/scoring/run/{project_id}")
def run_scoring(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    subject = session.exec(
        select(SubjectAsset).where(SubjectAsset.project_id == project_id)
    ).first()
    if not subject:
        raise HTTPException(status_code=400, detail="Subject asset not found for project")

    eligibles = session.exec(
        select(EligibleCandidate)
        .join(RawCandidate, EligibleCandidate.raw_candidate_id == RawCandidate.id)
        .where(RawCandidate.project_id == project_id)
        .where(EligibleCandidate.passed_hard_filter)
    ).all()

    top10s = session.exec(
        select(Top10Recommendation).where(Top10Recommendation.project_id == project_id)
    ).all()
    for t in top10s:
        session.delete(t)

    elig_ids = [el.id for el in eligibles]
    if elig_ids:
        scorings = session.exec(
            select(ScoringResult).where(ScoringResult.eligible_candidate_id.in_(elig_ids))
        ).all()
        for sc in scorings:
            session.delete(sc)

    candidates = session.exec(
        select(RawCandidate).where(RawCandidate.project_id == project_id)
    ).all()
    for c in candidates:
        if c.candidate_class == CandidateClass.RECOMMENDED_TOP_10:
            c.candidate_class = CandidateClass.RAW_CANDIDATE
            session.add(c)
    session.commit()

    eligibles = session.exec(
        select(EligibleCandidate)
        .join(RawCandidate, EligibleCandidate.raw_candidate_id == RawCandidate.id)
        .where(RawCandidate.project_id == project_id)
        .where(EligibleCandidate.passed_hard_filter)
    ).all()

    scored_items = []
    for el in eligibles:
        candidate = session.get(RawCandidate, el.raw_candidate_id)
        ext = session.exec(
            select(ExtractionResult).where(ExtractionResult.raw_candidate_id == candidate.id)
        ).first()

        orig = {
            "market_area": candidate.market_area,
            "land_type": candidate.land_type,
            "planning_segment": candidate.planning_segment,
            "size_sqm": candidate.size_sqm,
            "unit_price": candidate.unit_price,
        }
        if ext:
            candidate.market_area = ext.normalized_market_area
            candidate.land_type = ext.normalized_land_type
            candidate.planning_segment = ext.normalized_planning_segment
            candidate.size_sqm = ext.normalized_size_sqm
            candidate.unit_price = ext.normalized_unit_price

        ratio = hard_filter_service.estimate_adjustment_ratio(candidate, subject)
        score_tuple = scoring_service.build_scoring_tuple(candidate, subject, ratio)
        total_score = sum(score_tuple)

        candidate.market_area = orig["market_area"]
        candidate.land_type = orig["land_type"]
        candidate.planning_segment = orig["planning_segment"]
        candidate.size_sqm = orig["size_sqm"]
        candidate.unit_price = orig["unit_price"]

        scored_items.append(
            {
                "eligible_candidate": el,
                "candidate": candidate,
                "score_tuple": score_tuple,
                "total_score": total_score,
                "adjustment_ratio": ratio,
            }
        )

    # Use settings to control top N
    from app.config import settings

    ranked_dicts = scoring_service.rank_eligible_candidates(
        scored_items, limit=settings.top_recommended_count
    )

    for _index, item in enumerate(scored_items):
        el = item["eligible_candidate"]
        scores = item["score_tuple"]
        scoring_result = ScoringResult(
            eligible_candidate_id=el.id,
            market_area_score=scores[0],
            land_type_score=scores[1],
            size_score=scores[2],
            unit_price_score=scores[3],
            source_link_score=scores[4],
            adjustment_ratio_score=scores[5],
            adjustment_ratio=item["adjustment_ratio"],
            total_score=item["total_score"],
        )
        session.add(scoring_result)

    session.commit()

    for rank_idx, item in enumerate(ranked_dicts):
        el = item["eligible_candidate"]
        candidate = item["candidate"]

        rec = Top10Recommendation(
            project_id=project_id,
            eligible_candidate_id=el.id,
            rank=rank_idx + 1,
            candidate_class=CandidateClass.RECOMMENDED_TOP_10,
        )
        session.add(rec)

        candidate.candidate_class = CandidateClass.RECOMMENDED_TOP_10
        session.add(candidate)

    session.commit()

    status = scoring_service.insufficient_data_status(len(eligibles))
    return {
        "project_id": project_id,
        "status": status,
        "eligible_count": len(eligibles),
        "recommended_count": len(ranked_dicts),
    }


# Top 10 Retrieval Route
@router.get("/top10/{project_id}")
def get_top10(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    recs = session.exec(
        select(Top10Recommendation)
        .where(Top10Recommendation.project_id == project_id)
        .order_by(Top10Recommendation.rank)
    ).all()

    results = []
    for r in recs:
        el = session.get(EligibleCandidate, r.eligible_candidate_id)
        candidate = session.get(RawCandidate, el.raw_candidate_id) if el else None
        score_res = (
            session.exec(
                select(ScoringResult).where(
                    ScoringResult.eligible_candidate_id == r.eligible_candidate_id
                )
            ).first()
            if el
            else None
        )

        results.append(
            {
                "rank": r.rank,
                "eligible_candidate_id": r.eligible_candidate_id,
                "candidate": (
                    {
                        "id": candidate.id,
                        "source_url": candidate.source_url,
                        "market_area": candidate.market_area,
                        "land_type": candidate.land_type,
                        "planning_segment": candidate.planning_segment,
                        "size_sqm": candidate.size_sqm,
                        "unit_price": candidate.unit_price,
                        "asking_price": candidate.asking_price,
                    }
                    if candidate
                    else None
                ),
                "scores": (
                    {
                        "market_area_score": score_res.market_area_score,
                        "land_type_score": score_res.land_type_score,
                        "size_score": score_res.size_score,
                        "unit_price_score": score_res.unit_price_score,
                        "source_link_score": score_res.source_link_score,
                        "adjustment_ratio_score": score_res.adjustment_ratio_score,
                        "adjustment_ratio": score_res.adjustment_ratio,
                        "total_score": score_res.total_score,
                    }
                    if score_res
                    else None
                ),
            }
        )

    return {"project_id": project_id, "recommendations": results}


# Final 3 Selection Route
@router.post("/projects/{project_id}/select-final3")
def create_final3_selection(
    project_id: int, selection_data: Final3SelectionCreate, session: SessionDep
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Clear previous selections for this project
    existing = session.exec(
        select(Final3Selection).where(Final3Selection.project_id == project_id)
    ).all()
    for s in existing:
        session.delete(s)
    session.commit()

    try:
        selections = selection_service.select_final3(
            session=session,
            project_id=project_id,
            eligible_candidate_ids=selection_data.eligible_candidate_ids,
            selected_by=selection_data.selected_by,
            override_reason=selection_data.override_reason,
        )
        return {
            "project_id": project_id,
            "selections": [
                {
                    "id": s.id,
                    "eligible_candidate_id": s.eligible_candidate_id,
                    "is_override": s.is_override,
                    "override_reason": s.override_reason,
                    "selected_by": s.selected_by,
                }
                for s in selections
            ],
        }
    except selection_service.InvalidFinal3Selection as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/projects/{project_id}/selections")
def get_final3_selections(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    selections = session.exec(
        select(Final3Selection).where(Final3Selection.project_id == project_id)
    ).all()
    results = []
    for s in selections:
        el = session.get(EligibleCandidate, s.eligible_candidate_id)
        candidate = session.get(RawCandidate, el.raw_candidate_id) if el else None
        results.append(
            {
                "id": s.id,
                "eligible_candidate_id": s.eligible_candidate_id,
                "is_override": s.is_override,
                "override_reason": s.override_reason,
                "selected_by": s.selected_by,
                "candidate": (
                    {
                        "id": candidate.id,
                        "source_url": candidate.source_url,
                        "market_area": candidate.market_area,
                        "land_type": candidate.land_type,
                        "planning_segment": candidate.planning_segment,
                        "size_sqm": candidate.size_sqm,
                        "unit_price": candidate.unit_price,
                    }
                    if candidate
                    else None
                ),
            }
        )
    return {"project_id": project_id, "selections": results}


# Original Export Route
@router.post("/export/{project_id}")
def export_project(project_id: int, session: SessionDep):
    record = export_service.export_project_audit_workbook(session, project_id)
    return {
        "project_id": project_id,
        "export_record_id": record.id,
        "file_path": record.file_path,
        "status": record.status,
    }


# Original Audit Log Route
@router.get("/audit-log/{project_id}")
def get_audit_log(project_id: int, session: SessionDep):
    logs = session.exec(select(AuditLog).where(AuditLog.project_id == project_id)).all()
    return {
        "project_id": project_id,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "actor": log.actor,
                "details_json": log.details_json,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


# Phase 3.4 — TSSS Brain Routes
@router.get("/projects/{project_id}/tsss-brain/status")
def tsss_brain_status(project_id: int, session: SessionDep):
    """Return TSSS Brain service status for a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    subject = session.exec(
        select(SubjectAsset).where(SubjectAsset.project_id == project_id)
    ).first()

    from app.config import settings as app_settings

    brain_info = {
        "project_id": project_id,
        "project_name": project.name,
        "has_subject_asset": subject is not None,
        "subject_asset_summary": (
            tsss_brain_service.build_tsss_search_brief(subject) if subject else None
        ),
        "omniroute_configured": bool(app_settings.omniroute_api_key),
    }
    return brain_info


@router.post("/projects/{project_id}/tsss-brain/suggest-queries")
async def tsss_brain_suggest_queries(project_id: int, session: SessionDep):
    """Generate search query suggestions using OmniRoute LLM.

    Returns search query strings and constraints:
      market_area, land_type, size range, price basis, source caution.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    subject = session.exec(
        select(SubjectAsset).where(SubjectAsset.project_id == project_id)
    ).first()
    if not subject:
        raise HTTPException(
            status_code=400,
            detail="Subject asset not found. Create a subject asset first.",
        )

    result = tsss_brain_service.suggest_search_queries(subject)
    return {
        "project_id": project_id,
        "result": result,
    }


@router.post("/projects/{project_id}/tsss-brain/extract-candidate")
async def tsss_brain_extract_candidate(
    project_id: int,
    request_data: TsssBrainExtractCandidateRequest,
    session: SessionDep,
):
    """Extract candidate fields from raw text using OmniRoute LLM.

    Accepts JSON:
      source_url: optional string
      raw_text: required string
      create_raw_candidate: bool default false

    If create_raw_candidate is true, creates a RawCandidate entry
    via the existing route pattern (does NOT bypass dedup/hard-filter/scoring).
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    subject = session.exec(
        select(SubjectAsset).where(SubjectAsset.project_id == project_id)
    ).first()
    if not subject:
        raise HTTPException(
            status_code=400,
            detail="Subject asset not found. Create a subject asset first.",
        )

    if not request_data.raw_text or not request_data.raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="raw_text is required and must not be empty.",
        )

    # Run LLM extraction
    extracted = tsss_brain_service.extract_candidate_from_raw_text(
        raw_text=request_data.raw_text,
        source_url=request_data.source_url,
        subject_asset=subject,
    )

    response_data = {
        "project_id": project_id,
        "extracted": extracted,
        "raw_candidate_created": False,
        "raw_candidate": None,
    }

    # Optionally create a RawCandidate using the existing service pattern
    if request_data.create_raw_candidate:
        try:
            # Default source_quality to MEDIUM if extraction did not provide it
            src_quality = extracted.get("source_quality") or "MEDIUM"
            candidate_obj = add_raw_candidate(
                session,
                project_id=project_id,
                source_url=request_data.source_url or extracted.get("source_url"),
                raw_text=request_data.raw_text,
                market_area=extracted.get("market_area"),
                land_type=extracted.get("land_type"),
                planning_segment=extracted.get("planning_segment"),
                size_sqm=extracted.get("size_sqm"),
                unit_price=extracted.get("unit_price"),
                asking_price=extracted.get("asking_price"),
                source_quality=src_quality,
            )
            response_data["raw_candidate_created"] = True
            response_data["raw_candidate"] = {
                "id": candidate_obj.id,
                "source_url": candidate_obj.source_url,
                "market_area": candidate_obj.market_area,
                "land_type": candidate_obj.land_type,
                "size_sqm": candidate_obj.size_sqm,
                "unit_price": candidate_obj.unit_price,
                "asking_price": candidate_obj.asking_price,
                "source_quality": candidate_obj.source_quality,
            }
        except RawPoolLimitExceeded as e:
            response_data["raw_candidate_error"] = str(e)
            response_data["warnings"] = extracted.get("warnings", []) + [str(e)]

    return response_data


# Original Health Route
@router.get("/gateway/health")
async def gateway_health():
    client = FreeLLMAPIClient()
    return await client.check_health()
