from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Gateway Service"
    user_service_url: str = "http://user-service:8000"
    auth_service_url: str = "http://auth-service:8000"

    class Config:
        env_file = ".env"

settings = Settings()
