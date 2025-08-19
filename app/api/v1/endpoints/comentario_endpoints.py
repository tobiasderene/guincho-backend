from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Comentario
from app.schemas.comentarios import ComentarioCreate, ComentarioOut

router = APIRouter()

@router.post("/", response_model=ComentarioOut, status_code=status.HTTP_201_CREATED)
def crear_comentario(comentario: ComentarioCreate, db: Session = Depends(get_db)):
    nuevo_comentario = Comentario(**comentario.dict())
    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)
    return nuevo_comentario

@router.get("/", response_model=List[ComentarioOut])
def obtener_comentarios(db: Session = Depends(get_db)):
    return db.query(Comentario).all()

@router.get("/publicacion/{id_publicacion}", response_model=List[ComentarioOut])
def obtener_comentarios_por_publicacion(id_publicacion: int, db: Session = Depends(get_db)):
    return db.query(Comentario).filter(Comentario.id_publicacion == id_publicacion).all()

@router.delete("/{id_comentario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_comentario(id_comentario: int, db: Session = Depends(get_db)):
    comentario = db.query(Comentario).filter(Comentario.id_comentario == id_comentario).first()
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    
    db.delete(comentario)
    db.commit()
