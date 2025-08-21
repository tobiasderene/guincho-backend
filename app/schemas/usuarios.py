from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING


class UsuarioBase(BaseModel):
    nombre_usuario: str
    password: str
    tipo_usuario: str

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(BaseModel):
    id_usuario: Optional[int]
    nombre_usuario: Optional[str]
    password: Optional[str]
    tipo_usuario: Optional[str]
    
class UsuarioOut(UsuarioBase):
    id_usuario: int

    model_config = {
        "from_attributes": True
    }
