from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING


class ImagenBase(BaseModel):
    descripcion_comentario: str
    id_usuario: int
    id_publicacion: int

class ImageCreate(ImagenBase):
    pass
    
class ImagenOut(ImagenBase):
    id_comentario: int

    model_config = {
        "from_attributes": True
    }
