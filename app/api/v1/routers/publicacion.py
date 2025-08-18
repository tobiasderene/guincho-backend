from fastapi import APIRouter
from app.api.v1.endpoints.publicacion_endpoints import router as publicacion_router

router = APIRouter()
router.include_router(publicacion_router, prefix="/publicacion", tags=["publicacion"])