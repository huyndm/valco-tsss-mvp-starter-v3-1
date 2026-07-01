from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.audit import AuditLog
from app.models.candidate import ExtractionResult, RawCandidate
from app.services import export_service
from app.services.extraction_service import run_extraction_for_project
from app.services.llm_client import FreeLLMAPIClient

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


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
            }
            for result in results
        ],
    }


@router.post("/export/{project_id}")
def export_project(project_id: int, session: SessionDep):
    record = export_service.export_project_audit_workbook(session, project_id)
    return {
        "project_id": project_id,
        "export_record_id": record.id,
        "file_path": record.file_path,
        "status": record.status,
    }


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


@router.get("/gateway/health")
async def gateway_health():
    client = FreeLLMAPIClient()
    return await client.check_health()
