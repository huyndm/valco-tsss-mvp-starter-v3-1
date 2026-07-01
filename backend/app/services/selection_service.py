import json
from datetime import datetime

from sqlmodel import Session

from app.config import settings
from app.models.audit import AuditLog
from app.models.candidate import EligibleCandidate, Final3Selection
from app.models.enums import CandidateClass


class InvalidFinal3Selection(Exception):
    pass


def select_final3(
    session: Session,
    project_id: int,
    eligible_candidate_ids: list[int],
    selected_by: str,
    override_reason: str | None = None,
) -> list[Final3Selection]:
    if not eligible_candidate_ids:
        raise InvalidFinal3Selection("At least one eligible candidate must be selected")
    if len(eligible_candidate_ids) > settings.final_main_count:
        raise InvalidFinal3Selection(
            f"Cannot select more than {settings.final_main_count} main TSSS"
        )
    if len(set(eligible_candidate_ids)) != len(eligible_candidate_ids):
        raise InvalidFinal3Selection("Duplicate eligible_candidate_id in final 3 selection")
    selections: list[Final3Selection] = []
    for eligible_id in eligible_candidate_ids:
        eligible = session.get(EligibleCandidate, eligible_id)
        if eligible is None:
            raise InvalidFinal3Selection(f"EligibleCandidate {eligible_id} not found")
        is_override = not eligible.passed_hard_filter
        if is_override and not override_reason:
            raise InvalidFinal3Selection("override_reason is required for rejected candidate")
        selection = Final3Selection(
            project_id=project_id,
            eligible_candidate_id=eligible_id,
            selected_by=selected_by,
            is_override=is_override,
            override_reason=override_reason if is_override else None,
            candidate_class=CandidateClass.MAIN_SELECTED_3,
        )
        session.add(selection)
        selections.append(selection)
    session.add(
        AuditLog(
            project_id=project_id,
            action="final3_selection",
            actor=selected_by,
            details_json=json.dumps(
                {
                    "eligible_candidate_ids": eligible_candidate_ids,
                    "override_reason": override_reason,
                }
            ),
            created_at=datetime.utcnow(),
        )
    )
    session.commit()
    for selection in selections:
        session.refresh(selection)
    return selections
