from fastapi import APIRouter

from service.models import HealthResponse

public_router = APIRouter()


@public_router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
