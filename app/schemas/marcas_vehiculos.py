from __future__ import annotations
from pydantic import BaseModel
from typing import Optional 
from typing import TYPE_CHECKING


class MarcaVehiculoBase(BaseModel):
    nombre_marca_vehiculo: str

class MarcaVehiculoCreate(MarcaVehiculoBase):
    pass

class MarcaVehiculosUpdate(BaseModel):
    nombre_marca_vehiculo: Optional[str]
    
class MarcaVehiculosOut(MarcaVehiculoBase):
    id_marca_vehiculo: int

    model_config = {
        "from_attributes": True
    }
