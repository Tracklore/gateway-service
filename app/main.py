from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
# Add shared-libs to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared-libs'))
from core.settings import settings
from app.api.routes import router as api_router, _client

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "WARNING"),  # Use WARNING level by default for production, configurable via environment variable
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gateway Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # Use specific allowed origins from settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Gateway Service starting up")
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Gateway Service shutting down")
    # Close the global HTTP client
    await _client.aclose()
