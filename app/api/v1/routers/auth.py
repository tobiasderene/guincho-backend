from fastapi import APIRouter
from app.api.v1.endpoints.login_endpoints import router as login_router

router = APIRouter()
router.include_router(login_router, prefix="/auth", tags=["auth"])