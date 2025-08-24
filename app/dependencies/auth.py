from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared-libs'))
from core.settings import settings
from typing import Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# JWT configuration from settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"

async def validate_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user information"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id, "payload": payload}
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT token"""
    return await validate_jwt(credentials)
