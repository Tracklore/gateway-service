from fastapi import APIRouter, Request, Response, Depends, WebSocket
from fastapi import status
from fastapi.exceptions import WebSocketException
from httpx import AsyncClient, TimeoutException, ConnectError
import httpx
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared-libs'))
from core.settings import settings
from app.dependencies.auth import get_current_user
from app.dependencies.ws_auth import validate_websocket_connection
from app.utils.circuit_breaker import circuit_breakers, CircuitBreaker, CircuitBreakerOpenException, CircuitState
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Global client for connection pooling
_GATEWAY_TIMEOUT = httpx.Timeout(settings.request_timeout, connect=settings.connect_timeout)
_client = AsyncClient(
    timeout=_GATEWAY_TIMEOUT,
    limits=httpx.Limits(
        max_connections=settings.max_connection_pool_size,
        max_keepalive_connections=settings.max_keepalive_connections,
        keepalive_expiry=settings.keepalive_expiry
    )
)

router = APIRouter()

# Define supported services
SUPPORTED_SERVICES = {
    "user": settings.user_service_url,
    "auth": settings.auth_service_url,
    "badge": settings.badge_service_url,
    "feed": settings.feed_service_url,
    "messaging": settings.messaging_service_url,
    "notification": settings.notification_service_url,
    "project": settings.project_service_url,
    "new": settings.new_service_url
}

# Initialize circuit breakers for each service
for service_name in SUPPORTED_SERVICES.keys():
    if service_name not in circuit_breakers:
        circuit_breakers[service_name] = CircuitBreaker(failure_threshold=3, timeout=30)

# Public routes (no authentication required)
@router.get("/health")
async def health_check():
    """
    Health check endpoint with detailed information
    """
    # Get circuit breaker statuses
    service_statuses = {}
    for service_name, service_url in SUPPORTED_SERVICES.items():
        circuit_breaker = circuit_breakers.get(service_name)
        status = "unknown"
        if circuit_breaker:
            if circuit_breaker.state == CircuitState.CLOSED:
                status = "healthy"
            elif circuit_breaker.state == CircuitState.OPEN:
                status = "unavailable"
            elif circuit_breaker.state == CircuitState.HALF_OPEN:
                status = "recovering"
        
        service_statuses[service_name] = {
            "url": service_url,
            "status": status
        }
    
    return {
        "status": "ok",
        "version": "1.0.0",
        "services": service_statuses
    }

# Public auth routes (no authentication required)
@router.api_route("/auth/signup", methods=["POST"])
@router.api_route("/auth/login", methods=["POST"])
@router.api_route("/auth/refresh", methods=["POST"])
async def auth_public_proxy(request: Request):
    """Proxy requests to auth service without authentication for public endpoints"""
    # For auth service, we need to forward the full path since it's registered with /auth prefix
    path = request.url.path.lstrip("/")
    return await _proxy_request(request, "auth", path)

# Auth routes that should be forwarded to auth service for token validation
@router.api_route("/auth/me", methods=["GET"])
@router.api_route("/auth/logout", methods=["POST"])
async def auth_token_validation_proxy(request: Request):
    """Proxy requests to auth service for endpoints that require token validation by auth service"""
    path = request.url.path.lstrip("/")
    return await _proxy_request(request, "auth", path)

# Protected routes (authentication required and validated by gateway)
@router.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to user service with authentication"""
    return await _proxy_request(request, "user", f"users/{path}")

@router.api_route("/auth/{path:path}", methods=["PUT", "DELETE"])
async def auth_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to auth service with authentication (excluding public endpoints and token validation endpoints)"""
    return await _proxy_request(request, "auth", path)

@router.api_route("/badge/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def badge_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to badge service with authentication"""
    return await _proxy_request(request, "badge", path)

@router.api_route("/feed/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def feed_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to feed service with authentication"""
    return await _proxy_request(request, "feed", path)

# Messaging Service Routes
@router.get("/api/v1/messaging/conversations")
async def get_conversations(request: Request, current_user: dict = Depends(get_current_user)):
    """Fetch all conversations for a user"""
    return await _proxy_request(request, "messaging", "api/v1/messaging/conversations")

@router.post("/api/v1/messaging/conversations")
async def create_conversation(request: Request, current_user: dict = Depends(get_current_user)):
    """Create a new conversation"""
    return await _proxy_request(request, "messaging", "api/v1/messaging/conversations")

@router.get("/api/v1/messaging/conversations/{conversation_id}")
async def get_conversation(request: Request, conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific conversation"""
    path = f"api/v1/messaging/conversations/{conversation_id}"
    return await _proxy_request(request, "messaging", path)

@router.put("/api/v1/messaging/conversations/{conversation_id}")
async def update_conversation(request: Request, conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Update a conversation"""
    path = f"api/v1/messaging/conversations/{conversation_id}"
    return await _proxy_request(request, "messaging", path)

@router.delete("/api/v1/messaging/conversations/{conversation_id}")
async def delete_conversation(request: Request, conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a conversation"""
    path = f"api/v1/messaging/conversations/{conversation_id}"
    return await _proxy_request(request, "messaging", path)

@router.get("/api/v1/messaging/conversations/{conversation_id}/messages")
async def get_messages(request: Request, conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get messages for a conversation"""
    path = f"api/v1/messaging/conversations/{conversation_id}/messages"
    return await _proxy_request(request, "messaging", path)

# WebSocket route for real-time messaging
@router.websocket("/api/v1/messaging/ws/{conversation_id}")
async def websocket_messaging_proxy(websocket: WebSocket, conversation_id: str):
    """WebSocket proxy for real-time messaging with authentication"""
    # Validate the WebSocket connection first
    try:
        # This will validate the token from query parameters or headers
        user = await validate_websocket_connection(websocket, conversation_id)
    except WebSocketException:
        # If authentication fails, close the connection
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return
    
    await websocket.accept()
    
    try:
        # Establish WebSocket connection to the messaging service
        import websockets
        from websockets.exceptions import ConnectionClosed
        import asyncio
        
        # Prepare the URL to the messaging service, preserving any query parameters
        messaging_service_url = SUPPORTED_SERVICES["messaging"]
        # We need to handle wss vs ws protocols
        ws_url = messaging_service_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/api/v1/messaging/ws/{conversation_id}"
        
        # Establish connection to the messaging service
        service_ws = await websockets.connect(ws_url)
        
        # Create tasks for bidirectional message forwarding
        async def forward_client_to_service():
            try:
                async for message in websocket.iter_text():
                    await service_ws.send(message)
            except ConnectionClosed:
                pass
            except Exception as e:
                logger.error(f"Error forwarding client to service: {str(e)}")
        
        async def forward_service_to_client():
            try:
                async for message in service_ws:
                    await websocket.send_text(message)
            except ConnectionClosed:
                pass
            except Exception as e:
                logger.error(f"Error forwarding service to client: {str(e)}")
        
        # Start both forwarding tasks
        client_to_service_task = asyncio.create_task(forward_client_to_service())
        service_to_client_task = asyncio.create_task(forward_service_to_client())
        
        # Wait for either task to complete (meaning one side disconnected)
        done, pending = await asyncio.wait(
            [client_to_service_task, service_to_client_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            
        # Close the service WebSocket connection
        await service_ws.close()
        
    except Exception as e:
        logger.error(f"WebSocket proxy error: {str(e)}")
        await websocket.close()

@router.api_route("/notification/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def notification_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to notification service with authentication"""
    return await _proxy_request(request, "notification", path)

@router.api_route("/project/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def project_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to project service with authentication"""
    return await _proxy_request(request, "project", path)

@router.api_route("/new/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def new_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to new service with authentication"""
    return await _proxy_request(request, "new", path)

async def _make_downstream_request(client: AsyncClient, method: str, url: str, headers: dict, data: bytes):
    """Helper function to make downstream requests"""
    return await client.request(
        method=method,
        url=url,
        headers=headers,
        content=data,
    )


async def _make_streaming_downstream_request(client: AsyncClient, method: str, url: str, headers: dict, request: Request):
    """Helper function to make downstream requests with streaming"""
    # Stream the request body to avoid loading it all into memory
    return await client.request(
        method=method,
        url=url,
        headers=headers,
        content=request.stream(),
    )

async def _proxy_request(request: Request, service: str, path: str):
    """Internal function to proxy requests to downstream services"""
    # Validate service
    if service not in SUPPORTED_SERVICES:
        logger.warning(f"Unsupported service requested: {service}")
        return Response(content="Service not found", status_code=404)
    
    # Get circuit breaker for this service
    circuit_breaker = circuit_breakers.get(service)
    
    try:
        # Check if circuit breaker is open
        if circuit_breaker and circuit_breaker.is_open():
            logger.warning(f"Circuit breaker is open for service {service}")
            return Response(content="Service Unavailable", status_code=503)
        
        service_url = SUPPORTED_SERVICES[service]
        
        # Include query parameters in the URL
        query_params = str(request.url).split("?", 1)[1] if "?" in str(request.url) else ""
        if query_params:
            url = f"{service_url}/{path}?{query_params}"
        else:
            url = f"{service_url}/{path}"
        
        # Remove host header to avoid issues with downstream services
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Check if request has a large payload that should be streamed
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size:  # Use setting for threshold
            logger.info(f"Streaming {request.method} request to {url} due to large payload size")
            
            # Make request to downstream service with streaming for large payloads
            if circuit_breaker:
                response = await circuit_breaker.call(
                    _make_streaming_downstream_request, _client, request.method, url, headers, request
                )
            else:
                response = await _make_streaming_downstream_request(_client, request.method, url, headers, request)
        else:
            # Get request body for smaller payloads
            data = await request.body()
            
            logger.info(f"Proxying {request.method} request to {url}")
            
            # Make request to downstream service with circuit breaker using the global client
            if circuit_breaker:
                response = await circuit_breaker.call(
                    _make_downstream_request, _client, request.method, url, headers, data
                )
            else:
                response = await _make_downstream_request(_client, request.method, url, headers, data)
        
        # Return response from downstream service
        return Response(
            content=response.content, 
            status_code=response.status_code, 
            headers=dict(response.headers)
        )
    except CircuitBreakerOpenException:
        logger.error(f"Circuit breaker is open for service {service}")
        return Response(content="Service Unavailable", status_code=503)
    except TimeoutException:
        logger.error(f"Timeout error when connecting to service {service}")
        return Response(content="Gateway Timeout", status_code=504)
    except ConnectError:
        logger.error(f"Connection error when connecting to service {service}")
        return Response(content="Bad Gateway", status_code=502)
    except Exception as e:
        logger.error(f"Unexpected error when connecting to service {service}: {str(e)}")
        return Response(content="Internal Server Error", status_code=500)