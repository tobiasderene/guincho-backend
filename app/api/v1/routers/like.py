from fastapi import APIRouter
from app.api.v1.endpoints.like_endpoints import router as like_router

router = APIRouter()
router.include_router(like_router, prefix="/like", tags=["like"])