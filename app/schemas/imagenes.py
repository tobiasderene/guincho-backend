from __future__ import annotations
from pydantic import BaseModel
from typing import Optional

class ImagenBase(BaseModel):
    id_publicacion: int
    url_foto: str
    numero_imagen: int

class ImageCreate(ImagenBase):
    pass

class ImagenOut(ImagenBase):
    id_imagen: int

    model_config = {
        "from_attributes": True
    }
