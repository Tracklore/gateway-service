from fastapi import WebSocket, WebSocketException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared-libs'))
from core.settings import settings
from urllib.parse import parse_qs

# JWT configuration from settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"

security = HTTPBearer()

async def get_current_user_from_websocket(websocket: WebSocket):
    """
    Extract and validate JWT token from WebSocket connection query parameters
    """
    # Get query parameters from the WebSocket connection URL
    query_params = parse_qs(websocket.query_params.get("token", ""))
    token = None
    
    # Extract token from query parameters - support both single value and list
    if query_params:
        token = query_params[0] if isinstance(query_params[0], str) else query_params[0][0] if query_params[0] else None
    
    # Alternative: Check if token is in a custom header
    if not token:
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Token not provided"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Could not validate credentials"
            )
        return {"user_id": user_id, "payload": payload}
    except JWTError:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Could not validate credentials"
        )

async def validate_websocket_connection(websocket: WebSocket, conversation_id: str):
    """
    Validate WebSocket connection by checking user access to the specific conversation
    This function would typically check if the user has permission to access the conversation
    For now, it just validates the JWT token
    """
    user = await get_current_user_from_websocket(websocket)
    # In a real implementation, you would check if user has access to this conversation_id
    # This might involve making an API call to a service to verify permissions
    return user