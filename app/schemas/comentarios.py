from __future__ import annotations
from pydantic import BaseModel, validator
from typing import Optional 
from typing import TYPE_CHECKING


class ComentarioBase(BaseModel):
    descripcion_comentario: str
    id_usuario: int
    id_publicacion: int
    
    @validator('descripcion_comentario')
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('El comentario no puede estar vacío')
        if len(v.strip()) > 1000:  # Límite de caracteres
            raise ValueError('El comentario no puede tener más de 1000 caracteres')
        return v.strip()

class ComentarioCreate(ComentarioBase):
    pass
    
class ComentarioOut(ComentarioBase):
    id_comentario: int
    # Campos calculados que se agregarán en el endpoint
    nombre_usuario: Optional[str] = None
    fecha_comentario: Optional[str] = None

    model_config = {
        "from_attributes": True
    }