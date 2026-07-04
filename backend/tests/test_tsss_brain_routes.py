"""Tests for Phase 3.4 TSSS Brain + OmniRoute integration.

Ensures:
- Status endpoint returns correctly with/without subject asset.
- Suggest queries does not crash and returns fallback when gateway unavailable.
- Extract candidate returns fallback when gateway unavailable.
- No direct provider call is used.
"""

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def _create_project_with_subject(client) -> int:
    """Helper: create project and subject asset, return project_id."""
    resp = client.post("/api/v1/projects", json={"name": "TSSS Brain Test"})
    proj_id = resp.json()["id"]
    client.post(
        f"/api/v1/projects/{proj_id}/subject-asset",
        json={
            "address": "456 Brain St",
            "market_area": "District 2",
            "land_type": "ODT",
            "planning_segment": "residential",
            "size_sqm": 100.0,
        },
    )
    return proj_id


def test_tsss_brain_status():
    """GET /tsss-brain/status returns project info and omniroute config state."""
    with TestClient(app) as client:
        # Create project WITHOUT subject asset
        resp = client.post("/api/v1/projects", json={"name": "Status Test"})
        proj_id = resp.json()["id"]

        # Get status without subject asset
        resp = client.get(f"/api/v1/projects/{proj_id}/tsss-brain/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == proj_id
        assert data["has_subject_asset"] is False
        assert data["subject_asset_summary"] is None
        assert "omniroute_configured" in data

        # Create subject asset and re-check
        client.post(
            f"/api/v1/projects/{proj_id}/subject-asset",
            json={
                "address": "123 Test",
                "market_area": "District 1",
                "land_type": "ONT",
                "planning_segment": "residential",
                "size_sqm": 80.0,
            },
        )
        resp = client.get(f"/api/v1/projects/{proj_id}/tsss-brain/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_subject_asset"] is True
        summary = data["subject_asset_summary"]
        assert summary is not None
        assert "subject_asset" in summary
        assert summary["subject_asset"]["address"] == "123 Test"
        assert summary["subject_asset"]["market_area"] == "District 1"


def test_tsss_brain_status_project_not_found():
    """Status endpoint returns 404 for non-existent project."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/projects/99999/tsss-brain/status")
        assert resp.status_code == 404


def test_suggest_queries_without_crash(monkeypatch):
    """POST /tsss-brain/suggest-queries returns fallback when gateway unavailable.

    Since OMNIROUTE_API_KEY is not set by default, the OmniRouteClient
    will raise GatewayUnavailableError, and the service should return
    a deterministic fallback with warnings.
    """
    # Ensure no API key is available (default is None)
    monkeypatch.setattr(settings, "omniroute_api_key", None)

    with TestClient(app) as client:
        proj_id = _create_project_with_subject(client)

        # Suggest queries - should not crash
        resp = client.post(f"/api/v1/projects/{proj_id}/tsss-brain/suggest-queries")
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        result = data["result"]
        # Should have fallback search_queries
        assert "search_queries" in result
        assert isinstance(result["search_queries"], list)
        assert len(result["search_queries"]) > 0
        # Should have warnings because gateway is unavailable
        assert "warnings" in result
        assert len(result["warnings"]) > 0
        # Warning should mention the gateway unavailability
        assert any("unavailable" in w.lower() or "gateway" in w.lower() for w in result["warnings"])


def test_suggest_queries_no_subject_asset():
    """Suggest queries returns 400 if no subject asset exists."""
    with TestClient(app) as client:
        resp = client.post("/api/v1/projects", json={"name": "No Subject"})
        proj_id = resp.json()["id"]

        resp = client.post(f"/api/v1/projects/{proj_id}/tsss-brain/suggest-queries")
        assert resp.status_code == 400
        assert "subject asset" in resp.json()["detail"].lower()


def test_extract_candidate_fallback_without_gateway(monkeypatch):
    """POST /tsss-brain/extract-candidate returns fallback when OmniRoute unavailable.

    Without an API key, the OmniRouteClient should raise GatewayUnavailableError
    and the service should return deterministic fallback with warnings.
    """
    monkeypatch.setattr(settings, "omniroute_api_key", None)

    with TestClient(app) as client:
        proj_id = _create_project_with_subject(client)

        # Extract candidate with raw_text
        resp = client.post(
            f"/api/v1/projects/{proj_id}/tsss-brain/extract-candidate",
            json={
                "source_url": "https://example.com/listing",
                "raw_text": "Bán nhà mặt tiền Đường Lê Văn Việt, Thủ Đức, 100m2, giá 5 tỷ",
                "create_raw_candidate": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "extracted" in data
        extracted = data["extracted"]
        # Should have warnings because gateway is unavailable
        assert "warnings" in extracted
        assert len(extracted["warnings"]) > 0
        assert any(
            "unavailable" in w.lower() or "gateway" in w.lower() for w in extracted["warnings"]
        )

        # Fields should be present (some may be null in fallback)
        for field in [
            "market_area",
            "land_type",
            "planning_segment",
            "size_sqm",
            "unit_price",
            "asking_price",
            "source_quality",
            "draft_note",
        ]:
            assert field in extracted

        # raw_candidate_created should be False since create_raw_candidate=False
        assert data["raw_candidate_created"] is False


def test_extract_candidate_empty_raw_text():
    """Extract candidate returns 400 for empty raw_text."""
    with TestClient(app) as client:
        proj_id = _create_project_with_subject(client)

        resp = client.post(
            f"/api/v1/projects/{proj_id}/tsss-brain/extract-candidate",
            json={
                "raw_text": "",
                "create_raw_candidate": False,
            },
        )
        assert resp.status_code == 400
        assert "raw_text" in resp.json()["detail"].lower()


def test_extract_candidate_no_subject_asset():
    """Extract candidate returns 400 if no subject asset exists."""
    with TestClient(app) as client:
        resp = client.post("/api/v1/projects", json={"name": "No Subject"})
        proj_id = resp.json()["id"]

        resp = client.post(
            f"/api/v1/projects/{proj_id}/tsss-brain/extract-candidate",
            json={
                "raw_text": "Some listing text",
                "create_raw_candidate": False,
            },
        )
        assert resp.status_code == 400
        assert "subject asset" in resp.json()["detail"].lower()


def test_extract_candidate_with_create_raw_candidate(monkeypatch):
    """When create_raw_candidate=True, a RawCandidate should be created.

    Since OmniRoute is unavailable, the extracted fields will be null,
    but the RawCandidate should still be created with raw_text and source_url.
    """
    monkeypatch.setattr(settings, "omniroute_api_key", None)

    with TestClient(app) as client:
        proj_id = _create_project_with_subject(client)

        resp = client.post(
            f"/api/v1/projects/{proj_id}/tsss-brain/extract-candidate",
            json={
                "source_url": "https://test.com/create",
                "raw_text": "Test listing for raw candidate creation",
                "create_raw_candidate": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["raw_candidate_created"] is True
        assert data["raw_candidate"] is not None
        assert data["raw_candidate"]["source_url"] == "https://test.com/create"


def test_extract_candidate_with_create_raw_candidate_populates_fields(monkeypatch):
    """When create_raw_candidate=True, extracted fields must populate RawCandidate.

    Uses Vietnamese listing text:
      "Bán đất Phước Long, TP Thủ Đức. Diện tích 120m2, đất ONT,
       giá bán 11.4 tỷ đồng, đơn giá khoảng 95 triệu đồng/m2, pháp lý sổ riêng."

    Expected (via deterministic fallback when OmniRoute is unavailable):
      - market_area should be parsed from text
      - land_type should be "ONT"
      - size_sqm should be 120
      - unit_price should be 95_000_000 (95 million VND/m²)
      - asking_price should be 11_400_000_000 (11.4 billion VND)
    """
    monkeypatch.setattr(settings, "omniroute_api_key", None)

    with TestClient(app) as client:
        proj_id = _create_project_with_subject(client)

        resp = client.post(
            f"/api/v1/projects/{proj_id}/tsss-brain/extract-candidate",
            json={
                "source_url": "https://example.com/phuoc-long",
                "raw_text": (
                    "Bán đất Phước Long, TP Thủ Đức. "
                    "Diện tích 120m2, đất ONT, giá bán 11.4 tỷ đồng, "
                    "đơn giá khoảng 95 triệu đồng/m2, pháp lý sổ riêng."
                ),
                "create_raw_candidate": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["raw_candidate_created"] is True
        assert data["raw_candidate"] is not None

        raw = data["raw_candidate"]
        # source_url must be preserved
        assert raw["source_url"] == "https://example.com/phuoc-long"

        # Extracted fields should be populated by deterministic fallback parser
        # market_area – should not be null (parsed from text)
        assert raw["market_area"] is not None, "market_area should not be null"
        # land_type should be "ONT"
        assert raw["land_type"] == "ONT", f"Expected ONT, got {raw['land_type']}"
        # size_sqm should be 120
        assert raw["size_sqm"] == 120, f"Expected 120, got {raw['size_sqm']}"
        # unit_price should be 95,000,000 VND/m²
        assert raw["unit_price"] == 95_000_000, f"Expected 95000000, got {raw['unit_price']}"
        # asking_price should be 11,400,000,000 VND
        assert raw["asking_price"] == 11_400_000_000, f"Expected 11400000000, got {raw['asking_price']}"

        # Also verify via GET /raw-candidates
        get_resp = client.get(f"/api/v1/projects/{proj_id}/raw-candidates")
        assert get_resp.status_code == 200
        candidates = get_resp.json()
        created = [c for c in candidates if c["source_url"] == "https://example.com/phuoc-long"]
        assert len(created) == 1
        c = created[0]
        assert c["land_type"] == "ONT"
        assert c["size_sqm"] == 120


def test_no_direct_provider_call(monkeypatch):
    """Ensure that the OmniRouteClient does not call provider APIs directly.

    This tests the assert_no_direct_provider_url guard built into OmniRouteClient.
    """
    import pytest

    from app.services.llm_client import BLOCKED_PROVIDER_DOMAINS, assert_no_direct_provider_url

    # All blocked domains should raise ValueError
    for domain in BLOCKED_PROVIDER_DOMAINS:
        try:
            assert_no_direct_provider_url(f"https://{domain}/v1/chat/completions")
            pytest.fail(f"Expected ValueError for blocked domain: {domain}")
        except ValueError:
            pass

    # Non-blocked domains should pass
    try:
        assert_no_direct_provider_url("http://localhost:20128/v1/chat/completions")
    except ValueError:
        pytest.fail("Localhost should not be blocked")

    # Test with OmniRouteClient
    monkeypatch.setattr(settings, "omniroute_api_key", "test-key")

    from app.services.omni_client import OmniRouteClient

    # Should raise ValueError for blocked URLs
    for domain in BLOCKED_PROVIDER_DOMAINS:
        try:
            OmniRouteClient(
                base_url=f"https://{domain}/v1",
                api_key="test-key",
            )
            pytest.fail(f"Expected ValueError for blocked domain: {domain}")
        except ValueError:
            pass
