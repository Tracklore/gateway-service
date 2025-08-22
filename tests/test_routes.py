import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_proxy_user_service(mocker):
    mocker.patch("app.api.routes.settings.user_service_url", "http://test-user-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.return_value.status_code = 200
    mock_client.return_value.__aenter__.return_value.request.return_value.content = b'{"message": "user service"}'
    mock_client.return_value.__aenter__.return_value.request.return_value.headers = {}

    response = client.get("/user/somepath")
    assert response.status_code == 200
    assert response.json() == {"message": "user service"}

def test_proxy_auth_service(mocker):
    mocker.patch("app.api.routes.settings.auth_service_url", "http://test-auth-service")
    mock_client = mocker.patch("app.api.routes.AsyncClient")
    mock_client.return_value.__aenter__.return_value.request.return_value.status_code = 200
    mock_client.return_value.__aenter__.return_value.request.return_value.content = b'{"message": "auth service"}'
    mock_client.return_value.__aenter__.return_value.request.return_value.headers = {}

    response = client.get("/auth/somepath")
    assert response.status_code == 200
    assert response.json() == {"message": "auth service"}
