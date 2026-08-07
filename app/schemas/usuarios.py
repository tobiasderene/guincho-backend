from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class UsuarioBase(BaseModel):
    nombre_usuario: str
    password: str
    tipo_usuario: str

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(BaseModel):
    nombre_usuario: Optional[str] = None
    password: Optional[str] = None

class UsuarioOut(BaseModel):
    id_usuario: int
    nombre_usuario: str

    model_config = {
        "from_attributes": True
    }
