from fastapi import APIRouter
from app.api.v1.endpoints.nacionalidad_vehiculo_endpoints import router as nacionalidad_vehiculo_router

router = APIRouter()
router.include_router(nacionalidad_vehiculo_router, prefix="/nacionalidad", tags=["nacionalidad"])