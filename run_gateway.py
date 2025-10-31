import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Set the environment variables
    os.environ["USER_SERVICE_URL"] = "http://localhost:8001"
    os.environ["AUTH_SERVICE_URL"] = "http://localhost:8002"
    os.environ["BADGE_SERVICE_URL"] = "http://localhost:8003"
    os.environ["FEED_SERVICE_URL"] = "http://localhost:8004"
    os.environ["MESSAGING_SERVICE_URL"] = "http://localhost:8005"
    os.environ["NOTIFICATION_SERVICE_URL"] = "http://localhost:8006"
    os.environ["PROJECT_SERVICE_URL"] = "http://localhost:8007"
    os.environ["NEW_SERVICE_URL"] = "http://localhost:8008"
    os.environ["JWT_SECRET_KEY"] = "your_secret_key"
    
    uvicorn.run(app, host="0.0.0.0", port=8000)