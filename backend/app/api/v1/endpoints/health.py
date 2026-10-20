from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.core.database import check_db_health
from app.schemas.health import HealthResponse, DatabaseHealth

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System and Database Health Check",
    description="Returns the operational status of the TaskFlow API and its PostgreSQL database connection.",
    tags=["Health"],
)
def get_health(response: Response, strict: bool = False) -> HealthResponse:
    """
    Checks backend health and probes the PostgreSQL database.
    If database connectivity fails:
      - If strict=True: sets HTTP 503 Service Unavailable
      - If strict=False: sets status to 'degraded' with HTTP 200 for diagnostics
    """
    db_info = check_db_health()
    db_status = db_info.get("status")
    
    if db_status == "connected":
        overall_status = "healthy"
    else:
        overall_status = "degraded"
        if strict:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=DatabaseHealth(**db_info),
        details={
            "debug": settings.DEBUG,
            "api_version": settings.API_V1_STR,
        },
    )


@router.get(
    "/ping",
    summary="Simple liveness probe",
    description="Returns a lightweight pong for rapid liveness checks.",
    tags=["Health"],
)
def ping() -> dict:
    return {"ping": "pong"}
