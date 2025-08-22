from fastapi import APIRouter, Request, Response
from httpx import AsyncClient
from core.settings import settings

router = APIRouter()

@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, service: str, path: str):
    async with AsyncClient() as client:
        url = f"{settings.user_service_url}/{path}" if service == "user" else f"{settings.auth_service_url}/{path}"
        headers = dict(request.headers)
        headers.pop("host", None)
        data = await request.body()
        
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=data,
        )
        
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))