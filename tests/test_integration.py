import pytest
import asyncio
import aiohttp
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.main import app
from core.settings import settings

client = TestClient(app)

class TestGatewayIntegration:
    """Integration tests for the Gateway Service"""
    
    def create_test_token(self, user_id="testuser123", expires_in_minutes=60):
        """Create a valid test JWT token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        payload = {
            "sub": user_id,
            "exp": expire.timestamp()
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    
    def test_health_check_integration(self):
        """Test the health check endpoint integration"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "services" in data
        
        # Check that all services are reported
        services = data["services"]
        expected_services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
        for service in expected_services:
            assert service in services
            assert "url" in services[service]
            assert "status" in services[service]
    
    def test_user_service_proxy_integration(self, mocker):
        """Test integration with user service proxy"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"user": "testuser"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        # Create a valid token
        token = self.create_test_token()
        
        # Make request to user service
        response = client.get("/user/profile", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == {"user": "testuser"}
        
        # Verify the request was made to the correct URL
        call_args = mock_client.return_value.__aenter__.return_value.request.call_args
        assert call_args[1]['method'] == 'GET'
        assert call_args[1]['url'] == f"{settings.user_service_url}/profile"
    
    def test_auth_service_proxy_integration(self, mocker):
        """Test integration with auth service proxy"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"token": "new-token"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        # Create a valid token
        token = self.create_test_token()
        
        # Make request to auth service
        response = client.post("/auth/login", 
                             json={"username": "test", "password": "pass"},
                             headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == {"token": "new-token"}
        
        # Verify the request was made to the correct URL
        call_args = mock_client.return_value.__aenter__.return_value.request.call_args
        assert call_args[1]['method'] == 'POST'
        assert call_args[1]['url'] == f"{settings.auth_service_url}/login"
    
    def test_all_services_proxy_integration(self, mocker):
        """Test integration with all services"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"result": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        # Create a valid token
        token = self.create_test_token()
        
        # Test all services
        services = ["user", "auth", "badge", "feed", "messaging", "notification", "project", "new"]
        for service in services:
            response = client.get(f"/{service}/test", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert response.json() == {"result": "success"}
    
    def test_unauthorized_access_blocked(self):
        """Test that unauthorized access is properly blocked"""
        # Try to access protected endpoint without token
        response = client.get("/user/profile")
        assert response.status_code == 403
        
        # Try with invalid token
        response = client.get("/user/profile", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401
    
    def test_cors_headers_integration(self):
        """Test that CORS headers are properly set in integration"""
        response = client.get("/health")
        
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"
        assert "access-control-allow-credentials" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_response_preservation_integration(self, mocker):
        """Test that responses are properly preserved from downstream services"""
        # Mock different response types
        test_cases = [
            (200, {"message": "success"}, "application/json"),
            (201, {"id": 123}, "application/json"),
            (400, {"error": "bad request"}, "application/json"),
            (404, {"error": "not found"}, "application/json"),
            (500, {"error": "server error"}, "application/json")
        ]
        
        for status_code, content, content_type in test_cases:
            # Mock the AsyncClient to return the specific response
            mock_client = mocker.patch("app.api.routes.AsyncClient")
            mock_response = AsyncMock()
            mock_response.status_code = status_code
            mock_response.content = json.dumps(content).encode()
            mock_response.headers = {"content-type": content_type}
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            # Create a valid token
            token = self.create_test_token()
            
            # Make request
            response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
            
            # Verify response is preserved
            assert response.status_code == status_code
            assert response.json() == content
            assert response.headers["content-type"].startswith(content_type)
    
    def test_request_body_preservation_integration(self, mocker):
        """Test that request bodies are properly preserved when proxying"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"received": "data"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        # Create a valid token
        token = self.create_test_token()
        
        # Test with JSON body
        test_data = {
            "name": "test item",
            "value": 42,
            "nested": {
                "field": "value"
            }
        }
        
        response = client.post("/user/create", 
                              json=test_data,
                              headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        
        # Verify the request body was passed through correctly
        call_args = mock_client.return_value.__aenter__.return_value.request.call_args
        assert json.loads(call_args[1]['content'].decode()) == test_data
    
    def test_query_parameters_preservation_integration(self, mocker):
        """Test that query parameters are properly preserved when proxying"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"results": []}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        # Create a valid token
        token = self.create_test_token()
        
        # Test with query parameters
        params = {
            "q": "search term",
            "limit": 10,
            "offset": 20,
            "sort": "name"
        }
        
        response = client.get("/user/search", 
                             params=params,
                             headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        
        # Verify the URL was constructed correctly with query parameters
        call_args = mock_client.return_value.__aenter__.return_value.request.call_args
        expected_url = f"{settings.user_service_url}/search"
        for key, value in params.items():
            assert f"{key}={value}" in call_args[1]['url']
    
    def test_headers_preservation_integration(self, mocker):
        """Test that headers are properly preserved when proxying"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        # Create a valid token
        token = self.create_test_token()
        
        # Make request with custom headers
        custom_headers = {
            "Authorization": f"Bearer {token}",
            "X-Custom-Header": "custom-value",
            "X-Request-ID": "12345"
        }
        
        response = client.get("/user/test", headers=custom_headers)
        
        assert response.status_code == 200
        
        # Verify custom headers were passed through
        call_args = mock_client.return_value.__aenter__.return_value.request.call_args
        passed_headers = call_args[1]['headers']
        
        # Custom headers should be present
        assert passed_headers.get('X-Custom-Header') == 'custom-value'
        assert passed_headers.get('X-Request-ID') == '12345'
        
        # Host header should be removed
        assert 'host' not in passed_headers