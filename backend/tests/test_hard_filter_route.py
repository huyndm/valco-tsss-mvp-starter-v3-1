from fastapi.testclient import TestClient

from app.main import app


def test_hard_filter_route():
    with TestClient(app) as client:
        # Create project
        resp = client.post("/api/v1/projects", json={"name": "Hard Filter Project"})
        proj_id = resp.json()["id"]

        # Create subject asset
        asset_data = {
            "address": "123 Main St",
            "market_area": "District 2",
            "land_type": "ODT",
            "planning_segment": "residential",
            "size_sqm": 100.0,
        }
        client.post(f"/api/v1/projects/{proj_id}/subject-asset", json=asset_data)

        # Post raw candidates
        candidates = [
            {
                # Candidate 1: matches subject perfectly
                "source_url": "https://filter.com/1",
                "market_area": "District 2",
                "land_type": "ODT",
                "planning_segment": "residential",
                "size_sqm": 100.0,
                "unit_price": 50000000.0,
                "source_quality": "strong",
            },
            {
                # Candidate 2: wrong market area
                "source_url": "https://filter.com/2",
                "market_area": "District 9",
                "land_type": "ODT",
                "planning_segment": "residential",
                "size_sqm": 100.0,
                "unit_price": 50000000.0,
                "source_quality": "strong",
            },
        ]
        client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=candidates)

        # Run hard filter
        resp = client.post(f"/api/v1/hard-filter/run/{proj_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_evaluated"] == 2
        assert data["passed_count"] == 1

        # Verify classes in raw candidate pool
        resp = client.get(f"/api/v1/projects/{proj_id}/raw-candidates")
        cands = resp.json()
        classes = {c["source_url"]: c["candidate_class"] for c in cands}
        assert classes["https://filter.com/1"] == "RAW_CANDIDATE"
        assert classes["https://filter.com/2"] == "REJECT"
