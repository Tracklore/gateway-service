import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import sys
import os
# Add shared-libs to Python path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared-libs'))
from app.main import app
from jose import jwt
# Import settings from the gateway service shared-libs
from core.settings import settings

client = TestClient(app)

def create_test_token():
    """Create a valid test JWT token"""
    payload = {"sub": "testuser123", "exp": 9999999999}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

def test_all_service_routes():
    """Test that all service routes are properly configured"""
    # Test health check endpoint
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "services" in data
    
    # Check that all expected services are in the health check
    expected_services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
    for service in expected_services:
        assert service in data["services"]

def test_route_registration():
    """Test that all routes are properly registered"""
    # Get the app routes
    routes = [route.path for route in app.routes]
    
    # Check that we have the expected routes
    expected_routes = [
        "/health",
        "/user/{path:path}",
        "/auth/{path:path}",
        "/badge/{path:path}",
        "/feed/{path:path}",
        "/messaging/{path:path}",
        "/notification/{path:path}",
        "/project/{path:path}",
        "/new/{path:path}"
    ]
    
    for route in expected_routes:
        # For parameterized routes, we need to check if the pattern exists
        if "{path:path}" in route:
            base_path = route.split("/{path:path}")[0]
            # Check if any route starts with the base path
            assert any(r.startswith(base_path) for r in routes), f"Route {route} not found"
        else:
            assert route in routes, f"Route {route} not found"

def test_service_url_configuration():
    """Test that all service URLs are properly configured"""
    # Check that all service URLs are configured with correct ports
    expected_urls = {
        "user_service_url": "http://user-service:8001",
        "auth_service_url": "http://auth-service:8002",
        "badge_service_url": "http://badge-service:8003",
        "feed_service_url": "http://feed-service:8004",
        "messaging_service_url": "http://messaging-service:8005",
        "notification_service_url": "http://notification-service:8006",
        "project_service_url": "http://project-service:8007",
        "new_service_url": "http://new-service:8008"
    }
    
    for attr, expected_url in expected_urls.items():
        assert getattr(settings, attr) == expected_url, f"{attr} should be {expected_url}"

@pytest.mark.asyncio
async def test_all_services_respond_with_valid_token(mocker):
    """Test that all services respond correctly when a valid token is provided"""
    # Mock the AsyncClient to return successful responses
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    # Create a valid token
    token = create_test_token()
    
    # Test all service endpoints
    services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
    
    for service in services:
        response = client.get(f"/{service}/test", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, f"Service {service} should respond with 200"

def test_all_services_reject_missing_token():
    """Test that all services reject requests without a token"""
    services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
    
    for service in services:
        response = client.get(f"/{service}/test")
        # Should return 403 for missing credentials
        assert response.status_code == 403, f"Service {service} should reject missing token with 403"

def test_all_services_reject_invalid_token():
    """Test that all services reject requests with an invalid token"""
    services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
    
    for service in services:
        response = client.get(f"/{service}/test", headers={"Authorization": "Bearer invalidtoken"})
        # Should return 401 for invalid token
        assert response.status_code == 401, f"Service {service} should reject invalid token with 401"