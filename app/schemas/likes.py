from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING


class LikesBase(BaseModel):
    id_usuario: int
    id_comentario: Optional[int] = None
    id_publicacion: Optional[int] = None

class LikesCreate(LikesBase):
    pass
    
class LikesOut(LikesBase):
    id_like: int

    model_config = {
        "from_attributes": True
    }
