from fastapi import APIRouter
from app.api.v1.endpoints.comentario_endpoints import router as comentario_router

router = APIRouter()
router.include_router(comentario_router, prefix="/comentario", tags=["comentario"])