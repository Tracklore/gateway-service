import pytest
from fastapi.testclient import TestClient
from jose import jwt
import sys
import os
# Add shared-libs to Python path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared-libs'))
from app.main import app
from core.settings import settings

client = TestClient(app)

def test_valid_jwt_token():
    """Test that a valid JWT token is accepted"""
    # Create a valid token
    payload = {"sub": "testuser123", "exp": 9999999999}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    
    # Make a request with the valid token
    response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
    # Should not return 401, but might return other status codes based on service availability
    assert response.status_code != 401

def test_invalid_jwt_token():
    """Test that an invalid JWT token is rejected"""
    # Make a request with an invalid token
    response = client.get("/user/test", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

def test_missing_jwt_token():
    """Test that a missing JWT token is rejected"""
    # Make a request without a token
    response = client.get("/user/test")
    assert response.status_code == 403  # FastAPI returns 403 for missing credentials

def test_expired_jwt_token():
    """Test that an expired JWT token is rejected"""
    # Create an expired token
    payload = {"sub": "testuser123", "exp": 1000000}  # Expired timestamp
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    
    # Make a request with the expired token
    response = client.get("/user/test", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}