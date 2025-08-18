from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import MarcaVehiculo
from app.schemas.marcas_vehiculos import MarcaVehiculoCreate, MarcaVehiculosUpdate, MarcaVehiculosOut

router = APIRouter()


@router.post("/", response_model=MarcaVehiculosOut, status_code=status.HTTP_201_CREATED)
def create_brand(
    marca: MarcaVehiculoCreate,
    db: Session = Depends(get_db),
):
    nueva_marca = MarcaVehiculo(**marca.dict())
    db.add(nueva_marca)
    db.commit()
    db.refresh(nueva_marca)
    return nueva_marca


@router.get("/", response_model=List[MarcaVehiculosOut])
def get_all_brands(db: Session = Depends(get_db)):
    return db.query(MarcaVehiculo).all()


@router.get("/{marca_id}", response_model=MarcaVehiculosOut)
def get_brand(marca_id: str, db: Session = Depends(get_db)):
    marca = db.query(MarcaVehiculo).filter(MarcaVehiculo.id_marca_vehiculo == marca_id).first()
    if not marca:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return marca


@router.put("/{marca_id}", response_model=MarcaVehiculosOut)
def update_brand(
    marca_id: str,
    marca_data: MarcaVehiculosUpdate,
    db: Session = Depends(get_db),
):
    marca = db.query(MarcaVehiculo).filter(MarcaVehiculo.id_marca_vehiculo == marca_id).first()
    if not marca:
        raise HTTPException(status_code=404, detail="Marca no encontrada")

    for key, value in marca_data.dict(exclude_unset=True).items():
        setattr(marca, key, value)

    db.commit()
    db.refresh(marca)
    return marca


@router.delete("/{marca_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(marca_id: str, db: Session = Depends(get_db)):
    marca = db.query(MarcaVehiculo).filter(MarcaVehiculo.id_marca_vehiculo == marca_id).first()
    if not marca:
        raise HTTPException(status_code=404, detail="Marca no encontrada")

    db.delete(marca)
    db.commit()
