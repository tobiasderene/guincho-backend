from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING


class CategoriaVehiculosBase(BaseModel):
    nombre_categoria_vehiculo: str

class CategoriaVehiculosCreate(CategoriaVehiculosBase):
    pass

class CategoriaVehiculosUpdate(BaseModel):
    id_categoria_vehiculo: Optional[int]
    nombre_categoria_vehiculo: Optional[str]
    
class CategoriaVehiculosOut(CategoriaVehiculosBase):
    id_categoria_vehiculo: int

    model_config = {
        "from_attributes": True
    }
