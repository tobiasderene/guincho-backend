from fastapi import APIRouter, Depends, UploadFile, HTTPException, Form, status, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from google.cloud import storage
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Publicacion, Imagen, Usuario, MarcaVehiculo, CategoriaVehiculo
from app.schemas.publicaciones import PublicacionCreate, PublicacionOut, PublicacionDetails
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
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Crear la publicación usando el ID del usuario logueado
        nueva = Publicacion(
            id_usuario=current_user["id"],
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

        # Subir imágenes
        for idx, file in enumerate(files):
            img_url = upload_to_gcs(file)
            nueva_img = Imagen(
                id_publicacion=nueva.id_publicacion,
                url_foto=img_url,
                imagen_portada=b'\x01' if idx == 0 else b'\x00'
            )
            db.add(nueva_img)

        db.commit()
        db.refresh(nueva)

        return {"id": nueva.id_publicacion, "titulo": nueva.titulo, "imagenes": [f.filename for f in files]}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoint paginado con filtros de búsqueda ---
@router.get("/", status_code=status.HTTP_200_OK)
async def listar_publicaciones(
    skip: int = Query(0, ge=0),      # desde qué registro empezar
    limit: int = Query(7, ge=1, le=50), # cuántos traer (máximo 50)
    marca: Optional[int] = Query(None),   # id_marca_vehiculo
    año: Optional[int] = Query(None),     # year_vehiculo  
    modelo: Optional[str] = Query(None),  # búsqueda LIKE en titulo
    categoria: Optional[int] = Query(None), # id_categoria_vehiculo (por si lo necesitas)
    db: Session = Depends(get_db)
):
    try:
        # 1️⃣ Construir query base
        query = db.query(Publicacion)
        
        # 2️⃣ Aplicar filtros dinámicamente
        if marca:
            query = query.filter(Publicacion.id_marca_vehiculo == marca)
        
        if año:
            query = query.filter(Publicacion.year_vehiculo == año)
        
        if modelo and modelo.strip():
            # Búsqueda insensible a mayúsculas/minúsculas
            query = query.filter(Publicacion.titulo.ilike(f"%{modelo.strip()}%"))
        
        if categoria:
            query = query.filter(Publicacion.id_categoria_vehiculo == categoria)
        
        # 3️⃣ Contar total CON filtros aplicados
        total = query.count()
        
        # 4️⃣ Aplicar paginación y ordenamiento
        publicaciones = (
            query
            .order_by(Publicacion.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # 5️⃣ Preparar resultado (solo portada y datos necesarios)
        resultados = []
        for pub in publicaciones:
            portada = (
                db.query(Imagen)
                .filter(
                    Imagen.id_publicacion == pub.id_publicacion,
                    Imagen.imagen_portada == b'\x01'
                )
                .first()
            )
            
            # Obtener nombres de marca y categoría para mostrar en las tarjetas
            marca_nombre = (
                db.query(MarcaVehiculo.nombre_marca_vehiculo)
                .filter(MarcaVehiculo.id_marca_vehiculo == pub.id_marca_vehiculo)
                .scalar()
            )
            
            categoria_nombre = (
                db.query(CategoriaVehiculo.nombre_categoria_vehiculo)
                .filter(CategoriaVehiculo.id_categoria_vehiculo == pub.id_categoria_vehiculo)
                .scalar()
            )
            
            resultados.append({
                "id": pub.id_publicacion,
                "titulo": pub.titulo,
                "descripcion_corta": pub.descripcion_corta,
                "url_portada": portada.url_foto if portada else None,
                "year_vehiculo": pub.year_vehiculo,
                "id_marca_vehiculo": pub.id_marca_vehiculo,
                "nombre_marca_vehiculo": marca_nombre,
                "id_categoria_vehiculo": pub.id_categoria_vehiculo,
                "nombre_categoria_vehiculo": categoria_nombre,
                "fecha_publicacion": pub.fecha_publicacion
            })

        # 6️⃣ Devolver total (con filtros) y resultados
        return {
            "total": total,
            "publicaciones": resultados,
            "filtros_aplicados": {
                "marca": marca,
                "año": año,
                "modelo": modelo,
                "categoria": categoria
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


@router.get("/{id_publicacion}", response_model=PublicacionDetails)
async def obtener_publicacion(
    id_publicacion: int,
    db: Session = Depends(get_db)
):
    # 1️⃣ Hacemos join con usuario, marca y categoría
    pub = (
        db.query(Publicacion, Usuario.nombre_usuario, MarcaVehiculo.nombre_marca_vehiculo, CategoriaVehiculo.nombre_categoria_vehiculo)
        .join(Usuario, Usuario.id_usuario == Publicacion.id_usuario)
        .join(MarcaVehiculo, MarcaVehiculo.id_marca_vehiculo == Publicacion.id_marca_vehiculo)
        .join(CategoriaVehiculo, CategoriaVehiculo.id_categoria_vehiculo == Publicacion.id_categoria_vehiculo)
        .filter(Publicacion.id_publicacion == id_publicacion)
        .first()
    )

    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    publicacion, nombre_usuario, nombre_marca, nombre_categoria = pub

    # 2️⃣ Portada
    portada = (
        db.query(Imagen)
        .filter(
            Imagen.id_publicacion == publicacion.id_publicacion,
            Imagen.imagen_portada == b'\x01'
        )
        .first()
    )

    # 3️⃣ Todas las imágenes
    imagenes = (
        db.query(Imagen)
        .filter(Imagen.id_publicacion == publicacion.id_publicacion)
        .all()
    )

    # 4️⃣ Devolver resultado
    return {
        "id": publicacion.id_publicacion,
        "id_usuario": publicacion.id_usuario,
        "nombre_usuario": nombre_usuario,
        "descripcion": publicacion.descripcion,
        "descripcion_corta": publicacion.descripcion_corta,
        "titulo": publicacion.titulo,
        "url": publicacion.url,
        "year_vehiculo": publicacion.year_vehiculo,
        "id_categoria_vehiculo": publicacion.id_categoria_vehiculo,
        "nombre_categoria_vehiculo": nombre_categoria,
        "id_marca_vehiculo": publicacion.id_marca_vehiculo,
        "nombre_marca_vehiculo": nombre_marca,
        "detalle": publicacion.detalle,
        "fecha_publicacion": publicacion.fecha_publicacion,
        "url_portada": portada.url_foto if portada else None,
        "imagenes": [img.url_foto for img in imagenes] if imagenes else []
    }

@router.delete("/{id_publicacion}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_publicacion(id_publicacion: int, db: Session = Depends(get_db)):
    pub = db.query(Publicacion).filter(Publicacion.id_publicacion == id_publicacion).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    db.delete(pub)
    db.commit()
