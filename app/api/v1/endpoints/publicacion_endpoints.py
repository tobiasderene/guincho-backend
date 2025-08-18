from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.db.models import Publicacion
from app.schemas.publicaciones import PublicacionCreate, PublicacionOut

router = APIRouter()

@router.post("/", response_model=PublicacionOut, status_code=status.HTTP_201_CREATED)
def crear_publicacion(publicacion: PublicacionCreate, db: Session = Depends(get_db)):
    nueva = Publicacion(
        **publicacion.dict(),
        fecha_publicacion=datetime.utcnow()
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get("/", response_model=List[PublicacionOut])
def listar_publicaciones(db: Session = Depends(get_db)):
    return db.query(Publicacion).order_by(Publicacion.fecha_publicacion.desc()).all()

@router.get("/{id_publicacion}", response_model=PublicacionOut)
def obtener_publicacion(id_publicacion: int, db: Session = Depends(get_db)):
    pub = db.query(Publicacion).filter(Publicacion.id_publicacion == id_publicacion).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    return pub

@router.delete("/{id_publicacion}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_publicacion(id_publicacion: int, db: Session = Depends(get_db)):
    pub = db.query(Publicacion).filter(Publicacion.id_publicacion == id_publicacion).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    db.delete(pub)
    db.commit()
