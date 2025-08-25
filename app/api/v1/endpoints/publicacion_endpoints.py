from fastapi import APIRouter, Depends, UploadFile, HTTPException, Form, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from google.cloud import storage
from app.db.database import get_db
from app.db.models import Publicacion
from app.db.models import Imagen
from app.schemas.publicaciones import PublicacionCreate, PublicacionOut
from app.schemas.imagenes import ImageCreate, ImagenOut

router = APIRouter()

import os
BUCKET_NAME = os.getenv("BUCKET_NAME")

# --- Helper para subir imagen ---
def upload_to_gcs(file: UploadFile):
    client = storage.Client()  # toma credenciales de GOOGLE_APPLICATION_CREDENTIALS
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(file.filename)

    blob.upload_from_file(file.file, content_type=file.content_type)
    # URL pública del bucket (si es público) o privada si UBLA
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{file.filename}"


# --- Endpoint unificado ---
@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_publicacion(
    titulo: str = Form(...),
    descripcion_corta: str = Form(...),
    descripcion: str = Form(...),
    detalle: str = Form(...),
    url: str = Form(None),
    year_vehiculo: int = Form(...),
    id_categoria_vehiculo: int = Form(...),
    id_marca_vehiculo: int = Form(...),
    id_usuario: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 1️⃣ Crear la publicación
        nueva = Publicacion(
            id_usuario=id_usuario,
            titulo=titulo,
            descripcion_corta=descripcion_corta,
            descripcion=descripcion,
            detalle=detalle,
            url=url,
            year_vehiculo=year_vehiculo,
            id_categoria_vehiculo=id_categoria_vehiculo,
            id_marca_vehiculo=id_marca_vehiculo,
            fecha_publicacion=datetime.utcnow()
        )
        db.add(nueva)
        db.commit()
        db.refresh(nueva)

        # 2️⃣ Subir imágenes y guardarlas en la DB
        for idx, file in enumerate(files):
            img_url = upload_to_gcs(file)
            nueva_img = Imagen(
                id_publicacion=nueva.id,
                url_foto=img_url,
                imagen_portada=(idx == 0)  # la primera imagen como portada
            )
            db.add(nueva_img)

        db.commit()
        db.refresh(nueva)

        return {"id": nueva.id, "titulo": nueva.titulo, "imagenes": [f.filename for f in files]}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[PublicacionOut])
def listar_publicaciones(db: Session = Depends(get_db)):
    publicaciones = db.query(Publicacion).all()
    return publicaciones


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
