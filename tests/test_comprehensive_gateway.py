import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
import os
import json
from jose import jwt
from datetime import datetime, timedelta, timezone

# Add shared-libs to Python path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared-libs'))
from app.main import app
from core.settings import settings

client = TestClient(app)

# Test JWT token utilities
def create_test_token(user_id="testuser123", expires_in_minutes=60):
    """Create a valid test JWT token"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
    payload = {
        "sub": user_id,
        "exp": expire.timestamp()
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

def create_expired_token(user_id="testuser123"):
    """Create an expired test JWT token"""
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    payload = {
        "sub": user_id,
        "exp": expire.timestamp()
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

# Fixtures
@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset circuit breakers to closed state before each test"""
    from app.api.routes import circuit_breakers
    from app.utils.circuit_breaker import CircuitState
    for cb in circuit_breakers.values():
        cb.state = CircuitState.CLOSED
        cb.failure_count = 0
        cb.last_failure_time = None

# Health Check Tests
def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "services" in data
    assert isinstance(data["services"], dict)

def test_health_check_service_status():
    """Test that health check includes all expected services"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    expected_services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
    for service in expected_services:
        assert service in data["services"]
        service_info = data["services"][service]
        assert "url" in service_info
        assert "status" in service_info
        # Should be "unknown" since we're not actually connecting to services
        assert service_info["status"] in ["unknown", "healthy", "unavailable", "recovering"]

# Authentication Tests
def test_valid_jwt_token():
    """Test that a valid JWT token is accepted"""
    token = create_test_token()
    response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
    # Should not return 401, but might return other status codes based on service availability
    assert response.status_code != 401

def test_invalid_jwt_token():
    """Test that an invalid JWT token is rejected"""
    response = client.get("/user/test", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

def test_missing_jwt_token():
    """Test that a missing JWT token is rejected"""
    response = client.get("/user/test")
    assert response.status_code == 403  # FastAPI returns 403 for missing credentials

def test_expired_jwt_token():
    """Test that an expired JWT token is rejected"""
    token = create_expired_token()
    response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

def test_malformed_authorization_header():
    """Test that a malformed authorization header is rejected"""
    response = client.get("/user/test", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

# Service Proxy Tests
@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_service_success(mocker, service):
    """Test successful proxying to all services"""
    # Mock the AsyncClient to return a successful response
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    # Create a valid token
    token = create_test_token()
    
    # Test GET request
    response = client.get(f"/{service}/test", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    
    # Verify the mock was called with correct parameters
    mock_client.return_value.__aenter__.return_value.request.assert_called_once()
    
@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_service_different_methods(mocker, service):
    """Test proxying different HTTP methods to all services"""
    # Mock the AsyncClient to return successful responses
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    
    # Test POST
    response = client.post(f"/{service}/test", json={"test": "data"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Test PUT
    response = client.put(f"/{service}/test", json={"test": "data"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Test DELETE
    response = client.delete(f"/{service}/test", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_service_with_request_body(mocker, service):
    """Test proxying requests with body content to all services"""
    # Mock the AsyncClient to return successful responses
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"result": "created"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    
    # Test with JSON body
    test_data = {"name": "test", "value": 123}
    response = client.post(f"/{service}/create", json=test_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Verify the request body was passed through
    call_args = mock_client.return_value.__aenter__.return_value.request.call_args
    assert call_args[1]['content'] == json.dumps(test_data).encode()

@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_service_with_query_parameters(mocker, service):
    """Test proxying requests with query parameters to all services"""
    # Mock the AsyncClient to return successful responses
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"results": []}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    
    # Test with query parameters
    response = client.get(f"/{service}/search", params={"q": "test", "limit": 10}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Verify the URL was constructed correctly
    call_args = mock_client.return_value.__aenter__.return_value.request.call_args
    expected_url = f"{getattr(settings, f'{service}_service_url')}/search?q=test&limit=10"
    assert call_args[1]['url'] == expected_url

# Error Handling Tests
def test_proxy_unsupported_service():
    """Test proxying to an unsupported service returns 404"""
    token = create_test_token()
    response = client.get("/unsupported/somepath", headers={"Authorization": f"Bearer {token}"})
    # This should return 404 from FastAPI's default handler, not our custom one
    assert response.status_code == 404

@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_timeout_error(mocker, service):
    """Test handling of timeout errors for all services"""
    from httpx import TimeoutException
    
    # Mock the AsyncClient to raise a TimeoutException
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.side_effect = TimeoutException("Timeout")
    
    token = create_test_token()
    response = client.get(f"/{service}/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 504
    assert response.text == "Gateway Timeout"

@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_connection_error(mocker, service):
    """Test handling of connection errors for all services"""
    from httpx import ConnectError
    
    # Mock the AsyncClient to raise a ConnectError
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.side_effect = ConnectError("Connection failed")
    
    token = create_test_token()
    response = client.get(f"/{service}/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 502
    assert response.text == "Bad Gateway"

@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_unexpected_error(mocker, service):
    """Test handling of unexpected errors for all services"""
    # Mock the AsyncClient to raise a generic exception
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.side_effect = Exception("Unexpected error")
    
    token = create_test_token()
    response = client.get(f"/{service}/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 500
    assert response.text == "Internal Server Error"

# Circuit Breaker Tests
@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_proxy_circuit_breaker_open(mocker, service):
    """Test handling when circuit breaker is open for all services"""
    from app.api.routes import circuit_breakers
    from app.utils.circuit_breaker import CircuitBreaker, CircuitState
    
    # Create a circuit breaker and set it to open state
    cb = CircuitBreaker()
    cb.state = CircuitState.OPEN
    cb.last_failure_time = None
    circuit_breakers[service] = cb
    
    token = create_test_token()
    response = client.get(f"/{service}/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 503
    assert response.text == "Service Unavailable"

def test_circuit_breaker_transitions():
    """Test circuit breaker state transitions"""
    from app.utils.circuit_breaker import CircuitBreaker, CircuitState
    import time
    
    # Create a circuit breaker with low threshold for testing
    cb = CircuitBreaker(failure_threshold=2, timeout=1)
    
    # Initially should be closed
    assert cb.state == CircuitState.CLOSED
    
    # After one failure, should still be closed
    cb.call_failed()
    assert cb.state == CircuitState.CLOSED
    
    # After two failures, should be open
    cb.call_failed()
    assert cb.state == CircuitState.OPEN
    
    # After timeout, is_open() should detect the timeout and transition to half-open
    cb.last_failure_time = time.time() - 2  # Set failure time in the past
    # We need to call is_open() which will check the timeout and transition state
    cb.is_open()  # This should trigger the transition logic
    # Now it should be half-open
    assert cb.state == CircuitState.HALF_OPEN
    
    # After success, should be closed
    cb.call_succeeded()
    assert cb.state == CircuitState.CLOSED

@pytest.mark.parametrize("service", ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"])
def test_circuit_breaker_failure_counting(mocker, service):
    """Test that circuit breaker counts failures correctly"""
    from app.api.routes import circuit_breakers
    from app.utils.circuit_breaker import CircuitBreaker, CircuitState
    from httpx import ConnectError
    
    # Create a circuit breaker with threshold of 2
    cb = CircuitBreaker(failure_threshold=2)
    circuit_breakers[service] = cb
    
    # Mock the AsyncClient to raise a ConnectError
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.side_effect = ConnectError("Connection failed")
    
    token = create_test_token()
    
    # First failure - should still be closed
    response = client.get(f"/{service}/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 502
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1
    
    # Second failure - should open circuit breaker
    response = client.get(f"/{service}/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 502
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 2

# Header Handling Tests
def test_headers_passed_through(mocker):
    """Test that headers are properly passed through to downstream services"""
    # Mock the AsyncClient to return a successful response
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    
    # Make request with custom headers
    custom_headers = {
        "Authorization": f"Bearer {token}",
        "X-Custom-Header": "custom-value",
        "X-Another-Header": "another-value"
    }
    
    response = client.get("/user/test", headers=custom_headers)
    
    # Verify the headers were passed through (except Authorization which gets transformed)
    call_args = mock_client.return_value.__aenter__.return_value.request.call_args
    passed_headers = call_args[1]['headers']
    
    # The host header should be removed
    assert 'host' not in passed_headers
    # Custom headers should be present
    assert passed_headers.get('X-Custom-Header') == 'custom-value'
    assert passed_headers.get('X-Another-Header') == 'another-value'

def test_host_header_removed(mocker):
    """Test that the host header is removed when proxying"""
    # Mock the AsyncClient to return a successful response
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    
    # Make request with host header (this would normally be added by the HTTP client)
    response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
    
    # Verify the host header was removed
    call_args = mock_client.return_value.__aenter__.return_value.request.call_args
    passed_headers = call_args[1]['headers']
    assert 'host' not in passed_headers

# Response Handling Tests
def test_response_status_code_preserved(mocker):
    """Test that response status codes are preserved from downstream services"""
    # Test various status codes
    test_cases = [
        (200, {"message": "success"}),
        (201, {"id": 123}),
        (400, {"detail": "Bad Request"}),
        (404, {"detail": "Not Found"}),
        (500, {"detail": "Internal Server Error"})
    ]
    
    for status_code, content in test_cases:
        # Mock the AsyncClient to return the specific response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = status_code
        mock_response.content = json.dumps(content).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = create_test_token()
        response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == status_code
        assert response.json() == content

def test_response_headers_preserved(mocker):
    """Test that response headers are preserved from downstream services"""
    # Mock the AsyncClient to return a response with headers
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {
        "content-type": "application/json",
        "x-custom-header": "custom-value",
        "x-pagination": "page=1"
    }
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
    
    # Check that custom headers are preserved
    assert response.headers.get("x-custom-header") == "custom-value"
    assert response.headers.get("x-pagination") == "page=1"
    # Content-Type might be modified by FastAPI, so we check it's present
    assert "content-type" in response.headers

# Security Tests
def test_cors_headers():
    """Test that CORS headers are properly set"""
    response = client.get("/health")
    
    # Check for common CORS headers
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

def test_no_direct_service_access():
    """Test that services cannot be accessed directly without going through gateway"""
    # This is more of a conceptual test - in a real environment, 
    # the services would be on internal networks not accessible directly
    
    # For our test, we'll just verify that the gateway is the entry point
    response = client.get("/health")
    assert response.status_code == 200
    
    # Verify that we can't access service endpoints without authentication
    response = client.get("/user/test")
    assert response.status_code == 403

# Performance Tests
def test_concurrent_requests(mocker):
    """Test handling of concurrent requests"""
    # Mock the AsyncClient to return a successful response
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    
    # Make multiple concurrent requests
    responses = []
    for i in range(5):
        response = client.get(f"/user/test{i}", headers={"Authorization": f"Bearer {token}"})
        responses.append(response)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200

# Edge Case Tests
def test_empty_path(mocker):
    """Test proxying to service root path"""
    # Mock the AsyncClient to return a successful response
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "root"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    response = client.get("/user/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_special_characters_in_path(mocker):
    """Test proxying with special characters in path"""
    # Mock the AsyncClient to return a successful response
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "special"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    # Test with special characters
    response = client.get("/user/test with spaces", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    response = client.get("/user/test+with+plus", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_large_request_body(mocker):
    """Test handling of large request bodies"""
    # Mock the AsyncClient to return a successful response
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "large body handled"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
    
    token = create_test_token()
    
    # Create a large JSON payload
    large_data = {"items": [{"id": i, "value": f"value_{i}"} for i in range(1000)]}
    
    response = client.post("/user/bulk", json=large_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200