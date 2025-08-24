from fastapi import APIRouter, Request, Response, Depends
from httpx import AsyncClient, TimeoutException, ConnectError
import httpx
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared-libs'))
from core.settings import settings
from app.dependencies.auth import get_current_user
from app.utils.circuit_breaker import circuit_breakers, CircuitBreaker, CircuitBreakerOpenException, CircuitState
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Define supported services
SUPPORTED_SERVICES = {
    "user": settings.user_service_url,
    "auth": settings.auth_service_url
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

# Protected routes (authentication required)
@router.api_route("/user/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to user service with authentication"""
    return await _proxy_request(request, "user", path)

@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(request: Request, path: str, current_user: dict = Depends(get_current_user)):
    """Proxy requests to auth service with authentication"""
    return await _proxy_request(request, "auth", path)

async def _make_downstream_request(client: AsyncClient, method: str, url: str, headers: dict, data: bytes):
    """Helper function to make downstream requests"""
    return await client.request(
        method=method,
        url=url,
        headers=headers,
        content=data,
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
        
        # Adding a timeout to prevent hanging requests
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with AsyncClient(timeout=timeout) as client:
            service_url = SUPPORTED_SERVICES[service]
            url = f"{service_url}/{path}"
            
            # Remove host header to avoid issues with downstream services
            headers = dict(request.headers)
            headers.pop("host", None)
            
            # Get request body
            data = await request.body()
            
            logger.info(f"Proxying {request.method} request to {url}")
            
            # Make request to downstream service with circuit breaker
            if circuit_breaker:
                response = await circuit_breaker.call(
                    _make_downstream_request, client, request.method, url, headers, data
                )
            else:
                response = await _make_downstream_request(client, request.method, url, headers, data)
            
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