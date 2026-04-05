"""API v1 module"""
from fastapi import APIRouter
from .auth import router as auth_router
from .projects import router as projects_router
from .candidates import router as candidates_router
from .dashboard import router as dashboard_router
from .investigation import router as investigation_router
from .comparison import router as comparison_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(candidates_router, tags=["candidates"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(investigation_router, tags=["investigation"])
api_router.include_router(comparison_router, tags=["comparison"])
