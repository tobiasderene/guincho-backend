from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class VehiculoBase(BaseModel):
    modelo_vehiculo: str
    id_categoria_vehiculo: int
    id_marca_vehiculo: int
    id_nacionalidad_vehiculo: int
    year: int

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoUpdate(BaseModel):
    modelo_vehiculo: Optional[str]
    id_categoria_vehiculo: Optional[int]
    id_marca_vehiculo: Optional[int]
    id_nacionalidad_vehiculo: Optional[int]
    year: Optional[int]
    
class VehiculoOut(VehiculoBase):
    id_vehiculo: int

    model_config = {
        "from_attributes": True
    }