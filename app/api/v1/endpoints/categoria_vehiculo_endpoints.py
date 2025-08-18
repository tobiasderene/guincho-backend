from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import CategoriaVehiculo
from app.schemas.categorias_vehiculos import CategoriaVehiculosCreate, CategoriaVehiculosUpdate, CategoriaVehiculosOut

router = APIRouter()


@router.post("/", response_model=CategoriaVehiculosOut, status_code=status.HTTP_201_CREATED)
def create_categoria(categoria: CategoriaVehiculosCreate, db: Session = Depends(get_db)):
    nueva_categoria = CategoriaVehiculo(**categoria.dict())
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)
    return nueva_categoria


@router.get("/", response_model=List[CategoriaVehiculosOut])
def get_all_categorias(db: Session = Depends(get_db)):
    return db.query(CategoriaVehiculo).all()


@router.get("/{categoria_id}", response_model=CategoriaVehiculosOut)
def get_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaVehiculo).filter(CategoriaVehiculo.id_categoria_vehiculo == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaVehiculosOut)
def update_categoria(
    categoria_id: int,
    categoria_data: CategoriaVehiculosUpdate,
    db: Session = Depends(get_db),
):
    categoria = db.query(CategoriaVehiculo).filter(CategoriaVehiculo.id_categoria_vehiculo == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    for key, value in categoria_data.dict(exclude_unset=True).items():
        setattr(categoria, key, value)

    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaVehiculo).filter(CategoriaVehiculo.id_categoria_vehiculo == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(categoria)
    db.commit()
