from fastapi.testclient import TestClient

from app.main import app


def test_dedup_route():
    with TestClient(app) as client:
        # Create project
        resp = client.post("/api/v1/projects", json={"name": "Dedup Project"})
        proj_id = resp.json()["id"]

        # Post duplicate candidates
        candidates = [
            {
                "source_url": "https://dup.com/1",
                "market_area": "District 2",
                "land_type": "ODT",
                "size_sqm": 100.0,
                "unit_price": 50000000.0,
            },
            {
                "source_url": "https://dup.com/1",  # Identical source_url -> duplicate
                "market_area": "District 2",
                "land_type": "ODT",
                "size_sqm": 100.0,
                "unit_price": 50000000.0,
            },
        ]
        client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=candidates)

        # Run deduplication
        resp = client.post(f"/api/v1/dedup/run/{proj_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["duplicate_count"] == 1
        assert len(data["duplicates"]) == 1

        # Check candidate class updates
        resp = client.get(f"/api/v1/projects/{proj_id}/raw-candidates")
        cands = resp.json()
        classes = [c["candidate_class"] for c in cands]
        assert "DUPLICATE" in classes
        assert "RAW_CANDIDATE" in classes
