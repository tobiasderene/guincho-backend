from fastapi import APIRouter
from app.api.v1.endpoints.usuario_endpoints import router as usuario_router

router = APIRouter()
router.include_router(usuario_router, prefix="/usuario", tags=["usuario"])