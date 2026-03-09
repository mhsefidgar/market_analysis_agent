import pytest
from fastapi.testclient import TestClient
from main import app, tasks_db

client = TestClient(app)

def test_submit_analysis():
    response = client.post("/api/v1/analyze", json={
        "product_name": "iPhone 15",
        "competitors": ["Samsung S24"],
        "market_segment": "Premium Smartphones"
    })
    
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "running"
    
def test_get_analysis_status_not_found():
    response = client.get("/api/v1/analyze/invalid-id")
    assert response.status_code == 404
