import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.mark.unit
def test_health_endpoint():
    """
    Test the health check endpoint.
    """
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data 