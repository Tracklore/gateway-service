from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Gateway Service"
    user_service_url: str = "http://user-service:8001"
    auth_service_url: str = "http://auth-service:8002"
    badge_service_url: str = "http://badge-service:8003"
    feed_service_url: str = "http://feed-service:8004"
    messaging_service_url: str = "http://messaging-service:8005"
    notification_service_url: str = "http://notification-service:8006"
    project_service_url: str = "http://project-service:8007"
    # New service
    new_service_url: str = "http://new-service:8008"
    jwt_secret_key: str = "your_secret_key"
    
    # Performance and optimization settings
    max_connection_pool_size: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: int = 60  # seconds
    request_timeout: float = 30.0
    connect_timeout: float = 10.0
    max_request_size: int = 10 * 1024 * 1024  # 10MB in bytes
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "https://tracklore.com", "https://www.tracklore.com"]

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
