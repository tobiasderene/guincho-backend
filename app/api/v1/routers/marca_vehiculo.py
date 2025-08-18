from fastapi import APIRouter
from app.api.v1.endpoints.marca_vehiculo_endpoints import router as marca_router

router = APIRouter()
router.include_router(marca_router, prefix="/marca", tags=["marca"])