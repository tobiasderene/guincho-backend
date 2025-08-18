from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING


class ComentarioBase(BaseModel):
    descripcion_comentario: str
    id_usuario: int
    id_publicacion: int

class ComentarioCreate(ComentarioBase):
    pass
    
class ComentarioOut(ComentarioBase):
    id_comentario: int

    model_config = {
        "from_attributes": True
    }
