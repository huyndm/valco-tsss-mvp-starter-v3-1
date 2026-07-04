from fastapi.testclient import TestClient

from app.main import app


def test_scoring_and_selection():
    with TestClient(app) as client:
        # Create project
        resp = client.post("/api/v1/projects", json={"name": "Scoring Project"})
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

        # Upload 12 eligible candidates (so we have enough to test top 10 limit)
        candidates = []
        for i in range(1, 13):
            candidates.append(
                {
                    "source_url": f"https://scoring.com/{i}",
                    "market_area": "District 2",
                    "land_type": "ODT",
                    "planning_segment": "residential",
                    "size_sqm": 100.0 + i,  # size slight deviation to have distinct scores
                    "unit_price": 50000000.0,
                    "source_quality": "strong",
                }
            )
        client.post(f"/api/v1/projects/{proj_id}/raw-candidates", json=candidates)

        # Run hard filter first to establish eligible pool
        resp = client.post(f"/api/v1/hard-filter/run/{proj_id}")
        assert resp.status_code == 200
        # All 12 should pass
        assert resp.json()["passed_count"] == 12

        # Run scoring
        resp = client.post(f"/api/v1/scoring/run/{proj_id}")
        assert resp.status_code == 200
        sc_data = resp.json()
        assert sc_data["eligible_count"] == 12
        assert sc_data["recommended_count"] == 10  # Capped at 10
        assert sc_data["status"] == "FULL_TOP_10"

        # Fetch top 10
        resp = client.get(f"/api/v1/top10/{proj_id}")
        assert resp.status_code == 200
        top10_data = resp.json()
        assert len(top10_data["recommendations"]) == 10
        # Ranks should be 1 to 10
        ranks = [r["rank"] for r in top10_data["recommendations"]]
        assert ranks == list(range(1, 11))

        # Select final 3
        # Select first 3 recommended eligible candidate IDs
        eligible_ids = [r["eligible_candidate_id"] for r in top10_data["recommendations"][:3]]
        resp = client.post(
            f"/api/v1/projects/{proj_id}/select-final3",
            json={
                "eligible_candidate_ids": eligible_ids,
                "selected_by": "test_analyst",
            },
        )
        assert resp.status_code == 200
        sel_data = resp.json()
        assert len(sel_data["selections"]) == 3

        # Retrieve selections
        resp = client.get(f"/api/v1/projects/{proj_id}/selections")
        assert resp.status_code == 200
        fetched_selections = resp.json()["selections"]
        assert len(fetched_selections) == 3
        assert fetched_selections[0]["selected_by"] == "test_analyst"
