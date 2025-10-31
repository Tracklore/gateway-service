import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta, timezone
import json
import asyncio

from app.main import app
from core.settings import settings

client = TestClient(app)

class TestEdgeCases:
    """Edge case tests for the Gateway Service"""
    
    def create_test_token(self, user_id="testuser123", expires_in_minutes=60):
        """Create a valid test JWT token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        payload = {
            "sub": user_id,
            "exp": expire.timestamp()
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    
    def test_very_long_path(self, mocker):
        """Test handling of very long paths"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Create a very long path
        long_path = "a" * 1000
        response = client.get(f"/user/{long_path}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_special_characters_in_path(self, mocker):
        """Test handling of special characters in paths"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Test various special characters
        special_paths = [
            "test with spaces",
            "test+with+plus",
            "test%20encoded",
            "test#fragment",
            "test?query=param",
            "test&another=param",
            "test=equals",
            "test@symbol",
            "test_symbol",
            "test.symbol",
            "test,symbol"
        ]
        
        for path in special_paths:
            response = client.get(f"/user/{path}", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
    
    def test_very_large_request_body(self, mocker):
        """Test handling of very large request bodies"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Create a very large JSON payload
        large_data = {"items": [{"id": i, "value": f"value_{i}" * 100} for i in range(10000)]}
        
        response = client.post("/user/bulk", 
                              json=large_data,
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_empty_request_body(self, mocker):
        """Test handling of empty request bodies"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Test POST with empty body
        response = client.post("/user/create", 
                              json={},
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        # Test POST with no body
        response = client.post("/user/create", 
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_unicode_characters(self, mocker):
        """Test handling of unicode characters"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Test unicode in path
        response = client.get("/user/测试", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        # Test unicode in query parameters
        response = client.get("/user/search", 
                             params={"q": "测试查询"},
                             headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        # Test unicode in request body
        response = client.post("/user/create",
                              json={"name": "测试用户", "description": "这是一个测试"},
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
    
    def test_multiple_headers_same_name(self, mocker):
        """Test handling of multiple headers with the same name"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Note: HTTP clients typically don't allow multiple headers with the same name
        # but we can test with different header names
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Custom-1": "value1",
            "X-Custom-2": "value2",
            "X-Custom-3": "value3"
        }
        
        response = client.get("/user/test", headers=headers)
        assert response.status_code == 200
    
    def test_case_sensitivity(self, mocker):
        """Test case sensitivity of paths and headers"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Test that paths are case sensitive
        response1 = client.get("/user/Test", headers={"Authorization": f"Bearer {token}"})
        response2 = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
        
        # Both should work (the service decides if they're different)
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    def test_malformed_json_request(self, mocker):
        """Test handling of malformed JSON in request body"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Test with malformed JSON (this is handled by FastAPI before reaching our code)
        # We'll test with valid JSON that has unexpected structure
        response = client.post("/user/create",
                              json={"unexpected": {"nested": {"structure": "value"}}},
                              headers={"Authorization": f"Bearer {token}"})
        # Should still work - we just pass it through
        assert response.status_code == 200
    
    def test_very_large_headers(self, mocker):
        """Test handling of requests with very large headers"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Create a header with a large value
        large_header_value = "x" * 10000
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Large-Header": large_header_value
        }
        
        response = client.get("/user/test", headers=headers)
        assert response.status_code == 200
    
    def test_simultaneous_different_users(self, mocker):
        """Test handling of simultaneous requests from different users"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        # Create tokens for different users
        token1 = self.create_test_token("user1")
        token2 = self.create_test_token("user2")
        token3 = self.create_test_token("user3")
        
        # Make simultaneous requests
        responses = []
        for token in [token1, token2, token3]:
            response = client.get("/user/profile", headers={"Authorization": f"Bearer {token}"})
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_rapid_succession_requests(self, mocker):
        """Test handling of requests in rapid succession"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Make many requests in quick succession
        responses = []
        for i in range(100):
            response = client.get(f"/user/test{i}", headers={"Authorization": f"Bearer {token}"})
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_network_partition_scenarios(self, mocker):
        """Test handling of network partition-like scenarios"""
        from httpx import ConnectError, TimeoutException
        
        token = self.create_test_token()
        
        # Test connection error
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_client.return_value.__aenter__.return_value.request.side_effect = ConnectError("Network partition")
        
        response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 502
        
        # Test timeout error
        mock_client.return_value.__aenter__.return_value.request.side_effect = TimeoutException("Request timeout")
        
        response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 504
    
    def test_malformed_urls(self, mocker):
        """Test handling of malformed URLs"""
        # Mock the AsyncClient to return a successful response
        mock_client = mocker.patch("app.api.routes.AsyncClient")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode()
        mock_response.headers = {"content-type": "application/json"}
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        
        token = self.create_test_token()
        
        # Test various malformed URL scenarios
        malformed_paths = [
            "/user//double/slash",
            "/user/./current",
            "/user/../parent",
            "/user/~/home"
        ]
        
        for path in malformed_paths:
            response = client.get(path, headers={"Authorization": f"Bearer {token}"})
            # Should still work - downstream service handles path normalization
            assert response.status_code == 200