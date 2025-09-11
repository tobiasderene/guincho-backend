from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING
from datetime import datetime


class PublicacionBase(BaseModel):
    id_usuario: int
    descripcion: str
    fecha_publicacion: datetime
    descripcion_corta: str
    titulo: str
    url: Optional[str]
    year_vehiculo: int
    id_categoria_vehiculo: int
    id_marca_vehiculo: int 
    detalle: str

class PublicacionCreate(PublicacionBase):
    pass

class PublicacionUpdate(BaseModel):
    id_usuario: Optional[int]
    descripcion: Optional[str]
    fecha_publicacion: Optional[datetime]
    descripcion_corta: Optional[str]
    titulo: Optional[str]
    url: Optional[str]
    year_vehiculo: Optional[int]
    id_categoria_vehiculo: Optional[int]
    id_marca_vehiculo: Optional[int]
    detalle: Optional[str]
    
class PublicacionOut(PublicacionBase):
    id_publicacion: int

    model_config = {
        "from_attributes": True
    }

class PublicacionDetails(BaseModel):
    id: int
    id_usuario: int
    nombre_usuario: str
    descripcion: str
    descripcion_corta: str
    titulo: str
    url: Optional[str]
    year_vehiculo: int
    id_categoria_vehiculo: int
    nombre_categoria_vehiculo: str
    id_marca_vehiculo: int
    nombre_marca_vehiculo: str
    detalle: str
    fecha_publicacion: datetime
    url_portada: Optional[str]
    imagenes: list[str] = []

    class Config:
        orm_mode = True

# En tu archivo de schemas
class ImagenDetalle(BaseModel):
    id_imagen: int
    url_foto: str
    is_portada: bool

class PublicacionEditDetails(BaseModel):
    id: int
    id_usuario: int
    nombre_usuario: str
    descripcion: str
    descripcion_corta: str
    titulo: str
    url: Optional[str]
    year_vehiculo: int
    id_categoria_vehiculo: int
    nombre_categoria_vehiculo: str
    id_marca_vehiculo: int
    nombre_marca_vehiculo: str
    detalle: Optional[str]
    fecha_publicacion: datetime
    url_portada: Optional[str]
    imagenes: List[ImagenDetalle] = []
