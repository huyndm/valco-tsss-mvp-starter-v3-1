from fastapi.testclient import TestClient

from app.main import app


def test_project_crud():
    with TestClient(app) as client:
        # Create project
        resp = client.post(
            "/api/v1/projects", json={"name": "Route Project", "description": "Desc"}
        )
        assert resp.status_code == 200
        proj = resp.json()
        assert proj["name"] == "Route Project"
        proj_id = proj["id"]

        # Get list
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        projects = resp.json()
        assert len(projects) >= 1
        assert any(p["id"] == proj_id for p in projects)

        # Get single
        resp = client.get(f"/api/v1/projects/{proj_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Route Project"

        # Get single non-existent
        resp = client.get("/api/v1/projects/999999")
        assert resp.status_code == 404


def test_project_subject_asset():
    with TestClient(app) as client:
        # Create project first
        resp = client.post("/api/v1/projects", json={"name": "Asset Project"})
        proj_id = resp.json()["id"]

        # Get subject asset (should be 404 since it's not set)
        resp = client.get(f"/api/v1/projects/{proj_id}/subject-asset")
        assert resp.status_code == 404

        # Create/Update subject asset
        asset_data = {
            "address": "456 Test Ave",
            "market_area": "District 2",
            "land_type": "ODT",
            "planning_segment": "residential",
            "size_sqm": 120.0,
        }
        resp = client.post(f"/api/v1/projects/{proj_id}/subject-asset", json=asset_data)
        assert resp.status_code == 200
        asset = resp.json()
        assert asset["address"] == "456 Test Ave"
        assert asset["project_id"] == proj_id

        # Get subject asset (should now be 200)
        resp = client.get(f"/api/v1/projects/{proj_id}/subject-asset")
        assert resp.status_code == 200
        assert resp.json()["address"] == "456 Test Ave"

        # Try to post to non-existent project
        resp = client.post("/api/v1/projects/999999/subject-asset", json=asset_data)
        assert resp.status_code == 404
