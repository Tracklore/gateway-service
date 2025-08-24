from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Gateway Service"
    user_service_url: str = "http://user-service:8000"
    auth_service_url: str = "http://auth-service:8000"
    jwt_secret_key: str = "your-super-secret-jwt-key"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
