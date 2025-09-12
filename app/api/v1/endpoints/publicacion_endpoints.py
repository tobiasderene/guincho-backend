from fastapi import APIRouter, Depends, UploadFile, HTTPException, Form, status, File, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from google.cloud import storage
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Publicacion, Imagen, Usuario, MarcaVehiculo, CategoriaVehiculo
from app.schemas.publicaciones import PublicacionCreate, PublicacionOut, PublicacionDetails, PublicacionEditDetails
from app.schemas.imagenes import ImageCreate, ImagenOut
from google.cloud.exceptions import NotFound
import os
import uuid
from urllib.parse import urlparse
from pathlib import Path

router = APIRouter()
BUCKET_NAME = os.getenv("BUCKET_NAME")

# --- Helper para subir imagen ---
def upload_to_gcs(file: UploadFile):
    client = storage.Client()  # credenciales de GOOGLE_APPLICATION_CREDENTIALS
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file.file, content_type=file.content_type)
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{file.filename}"


# --- Crear publicación ---
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


# --- Listar publicaciones ---
@router.get("/", status_code=status.HTTP_200_OK)
async def listar_publicaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(7, ge=1, le=50),
    marca: Optional[int] = Query(None),
    año: Optional[int] = Query(None),
    modelo: Optional[str] = Query(None),
    categoria: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Publicacion)

        if marca:
            query = query.filter(Publicacion.id_marca_vehiculo == marca)
        if año:
            query = query.filter(Publicacion.year_vehiculo == año)
        if modelo and modelo.strip():
            query = query.filter(Publicacion.titulo.ilike(f"%{modelo.strip()}%"))
        if categoria:
            query = query.filter(Publicacion.id_categoria_vehiculo == categoria)

        total = query.count()
        publicaciones = (
            query.order_by(Publicacion.fecha_publicacion.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

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

        return {"total": total, "publicaciones": resultados}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


# --- Obtener publicación detalle ---
@router.get("/{id_publicacion}", response_model=PublicacionDetails)
async def obtener_publicacion(id_publicacion: int, db: Session = Depends(get_db)):
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

    portada = (
        db.query(Imagen)
        .filter(Imagen.id_publicacion == publicacion.id_publicacion, Imagen.imagen_portada == b'\x01')
        .first()
    )
    imagenes = db.query(Imagen).filter(Imagen.id_publicacion == publicacion.id_publicacion).all()

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


# --- PUT: actualizar publicación ---
@router.put("/{id}")
async def actualizar_publicacion(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        form = await request.form()
        nueva_portada = form.get('nueva_portada')
        mantener_imagenes = form.get('mantener_imagenes', '')
        files = request.form.getlist('files') if 'files' in form else []

        # Quitar portada de todas las imágenes existentes
        db.query(Imagen).filter(Imagen.id_publicacion == id).update({Imagen.imagen_portada: b'\x00'})

        # Mantener imágenes
        keep_ids = []
        if mantener_imagenes:
            keep_ids = [int(x.strip()) for x in mantener_imagenes.split(',') if x.strip()]
            if keep_ids:
                db.query(Imagen).filter(
                    Imagen.id_publicacion == id,
                    ~Imagen.id_imagen.in_(keep_ids)
                ).delete(synchronize_session=False)
            else:
                db.query(Imagen).filter(Imagen.id_publicacion == id).delete(synchronize_session=False)

        # Insertar nuevas imágenes
        nueva_imagen_ids = []
        for i, file in enumerate(files):
            file_url = await save_image_file(file)
            nueva_img = Imagen(
                id_publicacion=id,
                url_foto=file_url,
                imagen_portada=b'\x00'
            )
            db.add(nueva_img)
            db.flush()
            nueva_imagen_ids.append(nueva_img.id_imagen)

        # Definir portada
        if nueva_portada:
            if nueva_portada == 'nueva_0' and nueva_imagen_ids:
                portada_id = nueva_imagen_ids[0]
            elif nueva_portada.isdigit() and int(nueva_portada) in keep_ids:
                portada_id = int(nueva_portada)
            else:
                portada_id = None

            if portada_id:
                db.query(Imagen).filter(Imagen.id_imagen == portada_id).update({Imagen.imagen_portada: b'\x01'})
        else:
            first = db.query(Imagen).filter(Imagen.id_publicacion == id).order_by(Imagen.id_imagen).first()
            if first:
                first.imagen_portada = b'\x01'

        db.commit()
        return {"mensaje": "Publicación actualizada correctamente", "id": id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando publicación: {str(e)}")


# --- Helper para guardar imágenes en disco (local) ---
async def save_image_file(file: UploadFile):
    file_extension = file.filename.split('.')[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    upload_dir = Path("uploads/images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    return f"/uploads/images/{unique_filename}"

# 🗑️ Helper para borrar archivos en Google Cloud Storage
def delete_from_gcs(file_url: str) -> bool:
    """
    Elimina un archivo de Google Cloud Storage usando su URL.

    Args:
        file_url (str): URL completa del archivo en GCS

    Returns:
        bool: True si se eliminó correctamente, False si hubo error
    """
    try:
        client = storage.Client()

        # Extraer bucket y blob de la URL
        # Ej: https://storage.googleapis.com/tu-bucket/carpeta/archivo.jpg
        parsed_url = urlparse(file_url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)
        if len(path_parts) < 2:
            print(f"URL inválida: {file_url}")
            return False

        bucket_name, blob_name = path_parts
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Eliminar archivo
        blob.delete()
        print(f"Archivo eliminado exitosamente: {blob_name}")
        return True

    except NotFound:
        print(f"Archivo no encontrado en GCS: {file_url}")
        return False
    except Exception as e:
        print(f"Error eliminando archivo de GCS: {str(e)}")
        return False


# 🗑️ Endpoint DELETE de publicaciones
@router.delete("/{id_publicacion}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_publicacion(
    id_publicacion: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una publicación (y sus imágenes asociadas).
    Solo el propietario puede eliminar su publicación.
    """
    try:
        # Buscar la publicación
        pub = (
            db.query(Publicacion)
            .filter(Publicacion.id_publicacion == id_publicacion)
            .first()
        )

        if not pub:
            raise HTTPException(status_code=404, detail="Publicación no encontrada")

        # Verificar propietario
        if pub.id_usuario != current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para eliminar esta publicación"
            )

        # Obtener imágenes asociadas
        imagenes = db.query(Imagen).filter(Imagen.id_publicacion == id_publicacion).all()

        # Eliminar imágenes (en GCS y en BD)
        for img in imagenes:
            try:
                ok = delete_from_gcs(img.url_foto)
                if not ok:
                    print(f"⚠️ No se pudo eliminar {img.url_foto} de GCS")
            except Exception as e:
                print(f"❌ Error eliminando {img.url_foto} de GCS: {e}")

            db.delete(img)

        # Eliminar la publicación
        db.delete(pub)
        db.commit()

        return  # 204 No Content

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
