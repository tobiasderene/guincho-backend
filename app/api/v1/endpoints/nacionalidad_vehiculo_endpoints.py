from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import NacionalidadVehiculo
from app.schemas.nacionalidades_vehiculos import NacionalidadVehiculoBase, NacionalidadVehiculoOut, NacionalidadVehiculoCreate, NacionalidadVehiculoUpdate

router = APIRouter()


@router.post("/", response_model=NacionalidadVehiculoOut, status_code=status.HTTP_201_CREATED)
def create_nacionalidad(
    nacionalidad: NacionalidadVehiculoCreate,
    db: Session = Depends(get_db),
):
    nueva = NacionalidadVehiculo(**nacionalidad.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/", response_model=List[NacionalidadVehiculoOut])
def get_all_nacionalidades(db: Session = Depends(get_db)):
    return db.query(NacionalidadVehiculo).all()


@router.get("/{nacionalidad_id}", response_model=NacionalidadVehiculoOut)
def get_nacionalidad(nacionalidad_id: int, db: Session = Depends(get_db)):
    nacionalidad = db.query(NacionalidadVehiculo).filter(NacionalidadVehiculo.id_nacionalidad_vehiculo == nacionalidad_id).first()
    if not nacionalidad:
        raise HTTPException(status_code=404, detail="Nacionalidad no encontrada")
    return nacionalidad


@router.put("/{nacionalidad_id}", response_model=NacionalidadVehiculoOut)
def update_nacionalidad(
    nacionalidad_id: int,
    nacionalidad_data: NacionalidadVehiculoUpdate,
    db: Session = Depends(get_db),
):
    nacionalidad = db.query(NacionalidadVehiculo).filter(NacionalidadVehiculo.id_nacionalidad_vehiculo == nacionalidad_id).first()
    if not nacionalidad:
        raise HTTPException(status_code=404, detail="Nacionalidad no encontrada")

    for key, value in nacionalidad_data.dict(exclude_unset=True).items():
        setattr(nacionalidad, key, value)

    db.commit()
    db.refresh(nacionalidad)
    return nacionalidad


@router.delete("/{nacionalidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nacionalidad(nacionalidad_id: int, db: Session = Depends(get_db)):
    nacionalidad = db.query(NacionalidadVehiculo).filter(NacionalidadVehiculo.id_nacionalidad_vehiculo == nacionalidad_id).first()
    if not nacionalidad:
        raise HTTPException(status_code=404, detail="Nacionalidad no encontrada")

    db.delete(nacionalidad)
    db.commit()
