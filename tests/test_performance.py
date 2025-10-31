import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
from jose import jwt
from datetime import datetime, timedelta, timezone
import json

from app.main import app
from core.settings import settings

client = TestClient(app)

class TestGatewayPerformance:
    """Performance tests for the Gateway Service"""
    
    def create_test_token(self, user_id="testuser123", expires_in_minutes=60):
        """Create a valid test JWT token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        payload = {
            "sub": user_id,
            "exp": expire.timestamp()
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    
    def test_single_request_performance(self, mocker):
        """Test the performance of a single request"""
        # Mock the AsyncClient to return a quick response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Measure request time
        start_time = time.time()
        response = client.get("/user/profile", headers={"Authorization": f"Bearer {token}"})
        end_time = time.time()
        
        # Verify response
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
        
        # Check that request was fast (should be under 100ms in test)
        request_time = end_time - start_time
        assert request_time < 0.1, f"Request took {request_time:.4f} seconds, which is too slow"
    
    def test_concurrent_requests_performance(self, mocker):
        """Test the performance of concurrent requests"""
        # Mock the AsyncClient to return a quick response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Make concurrent requests
        num_requests = 10
        start_time = time.time()
        
        responses = []
        for i in range(num_requests):
            response = client.get(f"/user/test{i}", headers={"Authorization": f"Bearer {token}"})
            responses.append(response)
        
        end_time = time.time()
        
        # Verify all responses
        for response in responses:
            assert response.status_code == 200
            assert response.json() == {"message": "success"}
        
        # Check that concurrent requests were handled efficiently
        total_time = end_time - start_time
        avg_time_per_request = total_time / num_requests
        assert avg_time_per_request < 0.1, f"Average time per request was {avg_time_per_request:.4f} seconds, which is too slow"
    
    def test_high_load_performance(self, mocker):
        """Test performance under high load"""
        # Mock the AsyncClient to return a quick response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Make a high number of requests
        num_requests = 50
        start_time = time.time()
        
        responses = []
        for i in range(num_requests):
            response = client.get(f"/user/test{i}", headers={"Authorization": f"Bearer {token}"})
            responses.append(response)
        
        end_time = time.time()
        
        # Verify all responses
        for response in responses:
            assert response.status_code == 200
            assert response.json() == {"message": "success"}
        
        # Check that high load was handled efficiently
        total_time = end_time - start_time
        avg_time_per_request = total_time / num_requests
        requests_per_second = num_requests / total_time
        
        print(f"High load test: {num_requests} requests in {total_time:.4f} seconds")
        print(f"Average time per request: {avg_time_per_request:.4f} seconds")
        print(f"Requests per second: {requests_per_second:.2f}")
        
        # Should handle at least 100 requests per second in test environment
        assert requests_per_second > 100, f"Only handled {requests_per_second:.2f} requests per second"
    
    def test_multiple_services_concurrent_performance(self, mocker):
        """Test performance when accessing multiple services concurrently"""
        # Mock the AsyncClient to return a quick response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Access multiple services
        services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
        start_time = time.time()
        
        responses = []
        for service in services:
            response = client.get(f"/{service}/test", headers={"Authorization": f"Bearer {token}"})
            responses.append(response)
        
        end_time = time.time()
        
        # Verify all responses
        for response in responses:
            assert response.status_code == 200
            assert response.json() == {"message": "success"}
        
        # Check performance
        total_time = end_time - start_time
        avg_time_per_request = total_time / len(services)
        assert avg_time_per_request < 0.1, f"Average time per request was {avg_time_per_request:.4f} seconds"
    
    def test_large_payload_performance(self, mocker):
        """Test performance with large payloads"""
        # Create a large response payload
        large_data = {"items": [{"id": i, "value": f"value_{i}"} for i in range(1000)]}
        
        # Mock the AsyncClient to return a large response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(large_data).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Measure request time for large payload
        start_time = time.time()
        response = client.get("/user/large-data", headers={"Authorization": f"Bearer {token}"})
        end_time = time.time()
        
        # Verify response
        assert response.status_code == 200
        assert response.json() == large_data
        
        # Check that even large payloads are handled efficiently
        request_time = end_time - start_time
        assert request_time < 1.0, f"Large payload request took {request_time:.4f} seconds"
    
    def test_error_handling_performance(self, mocker):
        """Test performance of error handling"""
        from httpx import ConnectError
        
        # Mock the AsyncClient to raise a ConnectError
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_client.return_value.__aenter__.return_value.request.side_effect = ConnectError("Connection failed")
        
        token = self.create_test_token()
        
        # Measure error handling time
        start_time = time.time()
        response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
        end_time = time.time()
        
        # Verify error response
        assert response.status_code == 502
        assert response.text == "Bad Gateway"
        
        # Check that error handling is fast
        error_handling_time = end_time - start_time
        assert error_handling_time < 0.1, f"Error handling took {error_handling_time:.4f} seconds"
    
    def test_circuit_breaker_performance(self, mocker):
        """Test performance with circuit breaker"""
        from app.api.routes import circuit_breakers
        from app.utils.circuit_breaker import CircuitBreaker, CircuitState
        from httpx import ConnectError
        
        # Create a circuit breaker and set it to open state
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.last_failure_time = None
        circuit_breakers["user"] = cb
        
        token = self.create_test_token()
        
        # Measure circuit breaker response time
        start_time = time.time()
        response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
        end_time = time.time()
        
        # Verify circuit breaker response
        assert response.status_code == 503
        assert response.text == "Service Unavailable"
        
        # Check that circuit breaker response is fast
        response_time = end_time - start_time
        assert response_time < 0.01, f"Circuit breaker response took {response_time:.4f} seconds"