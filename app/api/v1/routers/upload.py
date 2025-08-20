from fastapi import APIRouter
from app.api.v1.endpoints.upload_endpoints import router as upload_router

router = APIRouter()
router.include_router(upload_router, prefix="/upload", tags=["upload"])