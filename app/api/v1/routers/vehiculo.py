from fastapi import APIRouter
from app.api.v1.endpoints.vehiculo_endpoints import router as vehiculos_router

router = APIRouter()
router.include_router(vehiculos_router, prefix="/vehiculo", tags=["vehiculo"])