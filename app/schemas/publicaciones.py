from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING
from datetime import datetime


class PublicacionBase(BaseModel):
    id_usuario: int
    id_vehiculo: int
    descripcion: str
    fecha_publicacion: datetime
    descripcion_corta: str
    titulo: str
    url: Optional[str]

class PublicacionCreate(PublicacionBase):
    pass

class PublicacionUpdate(BaseModel):
    id_usuario: Optional[int]
    id_vehiculo: Optional[int]
    descripcion: Optional[str]
    fecha_publicacion: Optional[datetime]
    descripcion_corta: Optional[str]
    titulo: Optional[str]
    url: Optional[str]
    
class PublicacionOut(PublicacionBase):
    id_publicacion: int

    model_config = {
        "from_attributes": True
    }
