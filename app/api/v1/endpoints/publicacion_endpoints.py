from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.db.models import Publicacion
from app.db.models import Imagen
from app.schemas.publicaciones import PublicacionCreate, PublicacionOut
from app.schemas.imagenes import ImageCreate, ImagenOut

router = APIRouter()

@router.post("/", response_model=PublicacionOut, status_code=status.HTTP_201_CREATED)
def crear_publicacion(publicacion: PublicacionCreate, db: Session = Depends(get_db)):
    # 1. Crear la publicación
    nueva = Publicacion(
        short_description=publicacion.short_description,
        long_description=publicacion.long_description,
        link=publicacion.link,
        fecha_publicacion=datetime.utcnow()
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    # 2. Guardar las imágenes relacionadas
    for img in publicacion.imagenes:
        nueva_img = Imagen(
            id_publicacion=nueva.id,
            url_foto=img.url_foto,
            imagen_portada=img.imagen_portada,
        )
        db.add(nueva_img)

    db.commit()
    db.refresh(nueva)

    return nueva

@router.get("/", response_model=List[PublicacionOut])
def listar_publicaciones(db: Session = Depends(get_db)):
    publicaciones = db.query(Publicacion).all()
    return publicaciones


@router.get("/{id_publicacion}", response_model=PublicacionOut)
def obtener_publicacion(id_publicacion: int, db: Session = Depends(get_db)):
    pub = db.query(Publicacion).filter(Publicacion.id == id_publicacion).first()
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
