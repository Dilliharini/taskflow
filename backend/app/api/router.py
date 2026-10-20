from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, notifications, projects, realtime

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects", "Tasks", "Comments", "Activity"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(realtime.router, prefix="/ws", tags=["Realtime"])
