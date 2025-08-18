from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING


class NacionalidadVehiculoBase(BaseModel):
    nombre_nacionalidad_vehiculo: str

class NacionalidadVehiculoCreate(NacionalidadVehiculoBase):
    pass

class NacionalidadVehiculoUpdate(BaseModel):
    nombre_nacionalidad_vehiculo: Optional[str]
    
class NacionalidadVehiculoOut(NacionalidadVehiculoBase):
    id_nacionalidad_vehiculo: int

    model_config = {
        "from_attributes": True
    }
