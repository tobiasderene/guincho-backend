from fastapi import APIRouter
from app.api.v1.routers import usuario, auth, categoria_vehiculo, comentario, like, marca_vehiculo, nacionalidad_vehiculo, publicacion, vehiculo


api_router = APIRouter()
api_router.include_router(usuario.router)
api_router.include_router(auth.router)
api_router.include_router(categoria_vehiculo.router)
api_router.include_router(comentario.router)
api_router.include_router(like.router)
api_router.include_router(marca_vehiculo.router)
api_router.include_router(nacionalidad_vehiculo.router)
api_router.include_router(publicacion.router)
api_router.include_router(vehiculo.router)