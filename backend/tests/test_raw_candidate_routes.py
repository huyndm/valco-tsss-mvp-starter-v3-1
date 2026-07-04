from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_raw_candidate_upload_and_list():
    with TestClient(app) as client:
        # Create project
        resp = client.post("/api/v1/projects", json={"name": "Raw Candidate Project"})
        proj_id = resp.json()["id"]

        # Post single candidate
        candidate_data = {
            "source_url": "https://rawtest.com/1",
            "raw_text": "Beautiful house in District 2",
            "market_area": "District 2",
            "land_type": "ODT",
            "size_sqm": 80.0,
            "unit_price": 40000000.0,
        }
        resp = client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=candidate_data)
        assert resp.status_code == 200
        obj = resp.json()
        assert obj["source_url"] == "https://rawtest.com/1"
        assert obj["project_id"] == proj_id

        # Post bulk candidates
        bulk_data = [
            {"source_url": "https://rawtest.com/2", "size_sqm": 90.0},
            {"source_url": "https://rawtest.com/3", "size_sqm": 100.0},
        ]
        resp = client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=bulk_data)
        assert resp.status_code == 200
        objs = resp.json()
        assert len(objs) == 2
        assert objs[0]["source_url"] == "https://rawtest.com/2"

        # Get list
        resp = client.get(f"/api/v1/projects/{proj_id}/raw-candidates")
        assert resp.status_code == 200
        candidates = resp.json()
        assert len(candidates) == 3
        urls = [c["source_url"] for c in candidates]
        assert "https://rawtest.com/1" in urls
        assert "https://rawtest.com/2" in urls
        assert "https://rawtest.com/3" in urls


def test_enriched_raw_candidate_response():
    """Verify that get_raw_candidates returns enriched fields (dedup_status,
    hard_filter_status, hard_filter_flags, adjustment_warnings)."""
    with TestClient(app) as client:
        # Create project
        resp = client.post("/api/v1/projects", json={"name": "Enriched Test"})
        proj_id = resp.json()["id"]

        # Create subject asset
        client.post(
            f"/api/v1/projects/{proj_id}/subject-asset",
            json={
                "address": "456 Test",
                "market_area": "District 2",
                "land_type": "ODT",
                "planning_segment": "residential",
                "size_sqm": 100.0,
            },
        )

        # Post a candidate
        client.post(
            f"/api/v1/projects/{proj_id}/raw-candidates",
            json={
                "source_url": "https://enrich.com/1",
                "market_area": "District 2",
                "land_type": "ODT",
                "size_sqm": 100.0,
                "unit_price": 50000000.0,
            },
        )

        # Run dedup and hard filter to create status records
        client.post(f"/api/v1/dedup/run/{proj_id}")
        client.post(f"/api/v1/hard-filter/run/{proj_id}")

        # Get enriched candidates
        resp = client.get(f"/api/v1/projects/{proj_id}/raw-candidates")
        assert resp.status_code == 200
        candidates = resp.json()
        assert len(candidates) == 1
        c = candidates[0]

        # Check enriched fields exist
        assert "dedup_status" in c
        assert "hard_filter_status" in c
        assert "hard_filter_flags" in c
        assert "adjustment_warnings" in c

        # The candidate should be unique and passed hard filter
        assert c["dedup_status"] == "unique"
        assert c["hard_filter_status"] == "passed"
        assert isinstance(c["hard_filter_flags"], list)
        assert isinstance(c["adjustment_warnings"], list)


def test_raw_candidate_limit(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(settings, "max_raw_candidates", 2)
        resp = client.post("/api/v1/projects", json={"name": "Limit Project"})
        proj_id = resp.json()["id"]

        c1 = {"source_url": "https://limit.com/1"}
        c2 = {"source_url": "https://limit.com/2"}
        c3 = {"source_url": "https://limit.com/3"}

        # Upload first 2
        resp = client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=c1)
        assert resp.status_code == 200
        resp = client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=c2)
        assert resp.status_code == 200

        # Try to upload 3rd (should return 400)
        resp = client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=c3)
        assert resp.status_code == 400
        assert "Raw candidate pool cap reached" in resp.json()["detail"]
