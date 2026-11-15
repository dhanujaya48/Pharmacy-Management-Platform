from fastapi import APIRouter, status, Response
from app.config import get_settings
from app.database import check_database_health

router = APIRouter(tags=["Health & Readiness"])
settings = get_settings()


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 if the web server process is alive and accepting connections.",
    status_code=status.HTTP_200_OK,
)
def get_health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 if the service and database dependency are ready for traffic. Returns 503 otherwise.",
)
def get_readiness(response: Response):
    db_healthy = check_database_health()
    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "ready": False,
        }

    return {
        "status": "ready",
        "database": "connected",
        "ready": True,
    }
