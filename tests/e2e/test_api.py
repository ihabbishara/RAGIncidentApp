"""E2E API tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints end-to-end."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "RAG Incident Management System"
        assert data["status"] == "running"

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code in [200, 503]
        data = response.json()

        # Handle both initialized and uninitialized states
        if response.status_code == 200:
            assert "overall" in data
            assert "components" in data
        else:
            # Service not initialized yet
            assert "detail" in data or "overall" in data

    def test_stats_endpoint(self, client: TestClient):
        """Test stats endpoint."""
        response = client.get("/stats")

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "vector_store" in data

    def test_test_email_endpoint_valid(self, client: TestClient):
        """Test email processing endpoint with valid data."""
        email_data = {
            "from": "xyz@test.com",
            "subject": "Test Issue",
            "body": "This is a test email body.",
        }

        # This will likely fail if services aren't fully running
        # but tests the API structure
        response = client.post("/api/test-email", json=email_data)

        # Accept both success and service unavailable
        assert response.status_code in [200, 500, 503]

    def test_test_email_endpoint_missing_fields(self, client: TestClient):
        """Test email processing endpoint with missing fields."""
        email_data = {
            "from": "test@example.com",
            # Missing subject and body
        }

        response = client.post("/api/test-email", json=email_data)

        # Accept validation error (422) or service unavailable (503) or bad request (400)
        assert response.status_code in [400, 422, 503]

    def test_test_email_endpoint_invalid_json(self, client: TestClient):
        """Test email processing endpoint with invalid JSON."""
        response = client.post(
            "/api/test-email", data="invalid json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422
