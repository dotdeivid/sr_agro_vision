from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .images import router as images_router
from .inference import router as inference_router
from .copernicus import router as copernicus_router
from .analysis import router as analysis_router
from .export import router as export_router
from .projects import router as projects_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(images_router, prefix="/images", tags=["Images"])
api_router.include_router(inference_router, prefix="/inference", tags=["Inference"])
api_router.include_router(copernicus_router, prefix="/copernicus", tags=["Copernicus"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])
