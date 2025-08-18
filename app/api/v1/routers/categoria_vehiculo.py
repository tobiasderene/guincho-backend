from fastapi import APIRouter
from app.api.v1.endpoints.categoria_vehiculo_endpoints import router as categoria_vehiculo_router

router = APIRouter()
router.include_router(categoria_vehiculo_router , prefix="/categoria", tags=["categoria"])