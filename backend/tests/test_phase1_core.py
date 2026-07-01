import pytest

from app.config import settings
from app.models.candidate import ExtractionResult
from app.services.dedup_service import detect_duplicates
from app.services.evidence_service import (
    RawPoolLimitExceeded,
    add_raw_candidate,
    count_raw_candidates,
)
from app.services.hard_filter_service import evaluate_hard_filter, run_hard_filter
from app.services.llm_client import FreeLLMAPIClient, assert_no_direct_provider_url
from app.services.scoring_service import (
    build_scoring_tuple,
    insufficient_data_status,
    rank_eligible_candidates,
    rank_top10,
)
from app.services.selection_service import InvalidFinal3Selection, select_final3


def test_gateway_policy():
    assert_no_direct_provider_url("http://localhost:3001/v1/chat/completions")
    with pytest.raises(ValueError):
        assert_no_direct_provider_url("https://api.openai.com/v1/chat/completions")
    with pytest.raises(ValueError):
        FreeLLMAPIClient(endpoint="https://api.anthropic.com/v1/messages")


def test_raw_pool_cap(session, project, monkeypatch):
    monkeypatch.setattr(settings, "max_raw_candidates", 2)
    add_raw_candidate(session, project.id, source_url="u1")
    add_raw_candidate(session, project.id, source_url="u2")
    with pytest.raises(RawPoolLimitExceeded):
        add_raw_candidate(session, project.id, source_url="u3")
    assert count_raw_candidates(session, project.id) == 2


def test_dedup_and_filter(session, project, subject_asset):
    a = add_raw_candidate(
        session,
        project.id,
        source_url="https://x.com/1",
        market_area="District 2",
        land_type="ODT",
        planning_segment="residential",
        size_sqm=100,
        unit_price=50_000_000,
        source_quality="strong",
    )
    b = add_raw_candidate(
        session,
        project.id,
        source_url="https://x.com/1",
        market_area="District 2",
        land_type="ODT",
        planning_segment="residential",
        size_sqm=100,
        unit_price=50_000_000,
        source_quality="strong",
    )
    duplicates = detect_duplicates(session, [a, b])
    assert len(duplicates) == 1
    assert b.candidate_class == "DUPLICATE"
    results = run_hard_filter(session, [a, b], subject_asset)
    assert len(results) == 1
    assert results[0].passed_hard_filter is True


def test_hard_filter_flags_adjustment(session, project, subject_asset):
    candidate = add_raw_candidate(
        session,
        project.id,
        source_url="https://x.com/a",
        market_area="District 2",
        land_type="ODT",
        size_sqm=100,
        unit_price=1,
        source_quality="strong",
    )
    passed, flags, ratio = evaluate_hard_filter(candidate, subject_asset, adjustment_ratio=0.41)
    assert not passed
    assert "expected_adjustment_over_40pct" in flags
    assert ratio == 0.41


def test_scoring_and_insufficient_status(subject_asset):
    class Candidate:
        market_area = "District 2"
        land_type = "ODT"
        planning_segment = "residential"
        size_sqm = 100
        unit_price = 1
        source_url = "https://x.com"

    tup = build_scoring_tuple(Candidate(), subject_asset, 0.1)
    ranked = rank_eligible_candidates([{"id": 1, "score_tuple": tup}], limit=1)
    assert ranked[0]["candidate_class"] == "RECOMMENDED_TOP_10"
    assert len(rank_top10([{"id": i, "total_score": i} for i in range(20)])) == 10
    assert insufficient_data_status(8) == "PARTIAL_ELIGIBLE_SHOWN"
    assert insufficient_data_status(1) == "INSUFFICIENT_EXPAND_OR_ANALYST_DECISION"


def test_final3_selection_and_stub_extraction(session, project, subject_asset):
    candidate = add_raw_candidate(
        session,
        project.id,
        source_url="https://x.com/1",
        market_area="District 2",
        land_type="ODT",
        size_sqm=100,
        unit_price=1,
        source_quality="strong",
    )
    records = run_hard_filter(session, [candidate], subject_asset)
    selections = select_final3(session, project.id, [records[0].id], selected_by="analyst_a")
    assert selections[0].candidate_class == "MAIN_SELECTED_3"
    with pytest.raises(InvalidFinal3Selection):
        select_final3(session, project.id, [records[0].id, records[0].id], selected_by="analyst_a")
    assert ExtractionResult(raw_candidate_id=1).extraction_status == "stub_pending"
