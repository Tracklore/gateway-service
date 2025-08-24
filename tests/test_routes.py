import pytest
from fastapi.testclient import TestClient
from httpx import TimeoutException, ConnectError
from unittest.mock import AsyncMock
import sys
import os
# Add shared-libs to Python path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared-libs'))
from app.main import app
from app.utils.circuit_breaker import CircuitBreaker, CircuitState
from jose import jwt
from core.settings import settings

client = TestClient(app)

def create_test_token():
    """Create a valid test JWT token"""
    payload = {"sub": "testuser123", "exp": 9999999999}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

def reset_circuit_breakers():
    """Reset circuit breakers to closed state for testing"""
    from app.api.routes import circuit_breakers
    for cb in circuit_breakers.values():
        cb.state = CircuitState.CLOSED
        cb.failure_count = 0
        cb.last_failure_time = None

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "services" in data

def test_proxy_user_service(mocker):
    reset_circuit_breakers()  # Reset before test
    mocker.patch("app.api.routes.settings.user_service_url", "http://test-user-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.return_value.status_code = 200
    mock_client.return_value.__aenter__.return_value.request.return_value.content = b'{"message": "user service"}'
    mock_client.return_value.__aenter__.return_value.request.return_value.headers = {}

    # Use a valid token for protected routes
    token = create_test_token()
    response = client.get("/user/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "user service"}

def test_proxy_auth_service(mocker):
    reset_circuit_breakers()  # Reset before test
    mocker.patch("app.api.routes.settings.auth_service_url", "http://test-auth-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.return_value.status_code = 200
    mock_client.return_value.__aenter__.return_value.request.return_value.content = b'{"message": "auth service"}'
    mock_client.return_value.__aenter__.return_value.request.return_value.headers = {}

    # Use a valid token for protected routes
    token = create_test_token()
    response = client.get("/auth/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "auth service"}

def test_proxy_unsupported_service():
    """Test proxying to an unsupported service returns 404"""
    reset_circuit_breakers()  # Reset before test
    # Use a valid token for protected routes
    token = create_test_token()
    response = client.get("/unsupported/somepath", headers={"Authorization": f"Bearer {token}"})
    # This should return 404 from FastAPI's default handler, not our custom one
    assert response.status_code == 404

def test_proxy_timeout_error(mocker):
    """Test handling of timeout errors"""
    reset_circuit_breakers()  # Reset before test
    mocker.patch("app.api.routes.settings.user_service_url", "http://test-user-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.side_effect = TimeoutException("Timeout")

    # Use a valid token for protected routes
    token = create_test_token()
    response = client.get("/user/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 504
    assert response.text == "Gateway Timeout"

def test_proxy_connection_error(mocker):
    """Test handling of connection errors"""
    reset_circuit_breakers()  # Reset before test
    mocker.patch("app.api.routes.settings.user_service_url", "http://test-user-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.side_effect = ConnectError("Connection failed")

    # Use a valid token for protected routes
    token = create_test_token()
    response = client.get("/user/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 502
    assert response.text == "Bad Gateway"

def test_proxy_circuit_breaker_open(mocker):
    """Test handling when circuit breaker is open"""
    reset_circuit_breakers()  # Reset before test
    mocker.patch("app.api.routes.settings.user_service_url", "http://test-user-service")
    # Mock circuit breaker to be open
    from app.api.routes import circuit_breakers
    # Create a real circuit breaker and set it to open state
    cb = CircuitBreaker()
    cb.state = CircuitState.OPEN
    cb.last_failure_time = None
    circuit_breakers["user"] = cb

    # Use a valid token for protected routes
    token = create_test_token()
    response = client.get("/user/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 503
    assert response.text == "Service Unavailable"

def test_proxy_unexpected_error(mocker):
    """Test handling of unexpected errors"""
    reset_circuit_breakers()  # Reset before test
    mocker.patch("app.api.routes.settings.user_service_url", "http://test-user-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.side_effect = Exception("Unexpected error")

    # Use a valid token for protected routes
    token = create_test_token()
    response = client.get("/user/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 500
    assert response.text == "Internal Server Error"

def test_proxy_different_http_methods(mocker):
    """Test proxying different HTTP methods"""
    reset_circuit_breakers()  # Reset before test
    mocker.patch("app.api.routes.settings.user_service_url", "http://test-user-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "success"}'
    mock_response.headers = {}
    mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

    token = create_test_token()
    
    # Test POST
    response = client.post("/user/somepath", json={"test": "data"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # Test PUT
    response = client.put("/user/somepath", json={"test": "data"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # Test DELETE
    response = client.delete("/user/somepath", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

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
