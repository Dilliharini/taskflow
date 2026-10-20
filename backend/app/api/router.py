from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, projects

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects", "Tasks", "Comments", "Activity"])
