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

        # Crear imágenes con número secuencial (la primera será la portada)
        for idx, file in enumerate(files):
            img_url = upload_to_gcs(file)
            nueva_img = Imagen(
                id_publicacion=nueva.id_publicacion,
                url_foto=img_url,
                numero_imagen=idx + 1  # Numeración desde 1
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
        
        # Ordenar por fecha de publicación descendente (más nuevo primero)
        # Agregamos también id_publicacion desc como criterio secundario para consistencia
        publicaciones = (
            query.order_by(
                Publicacion.fecha_publicacion.desc(),
                Publicacion.id_publicacion.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        resultados = []
        for pub in publicaciones:
            # Buscar la imagen portada (la primera imagen: numero_imagen = 1)
            portada = (
                db.query(Imagen)
                .filter(
                    Imagen.id_publicacion == pub.id_publicacion,
                    Imagen.numero_imagen == 1
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

    # La portada es la primera imagen (numero_imagen = 1)
    portada = (
        db.query(Imagen)
        .filter(
            Imagen.id_publicacion == publicacion.id_publicacion,
            Imagen.numero_imagen == 1
        )
        .first()
    )
    
    # Obtener imágenes ordenadas por numero_imagen
    imagenes = (
        db.query(Imagen)
        .filter(Imagen.id_publicacion == publicacion.id_publicacion)
        .order_by(Imagen.numero_imagen)
        .all()
    )

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

# Obtener publicación para editar (incluye IDs de imagen y numero_imagen)
@router.get("/edit-post/{id_publicacion}", response_model=PublicacionEditDetails)
async def obtener_publicacion_para_editar(id_publicacion: int, db: Session = Depends(get_db)):
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

    # La portada es la primera imagen (numero_imagen = 1)
    portada = (
        db.query(Imagen)
        .filter(
            Imagen.id_publicacion == publicacion.id_publicacion,
            Imagen.numero_imagen == 1
        )
        .first()
    )
    
    # Obtener imágenes ordenadas por numero_imagen
    imagenes = (
        db.query(Imagen)
        .filter(Imagen.id_publicacion == publicacion.id_publicacion)
        .order_by(Imagen.numero_imagen)
        .all()
    )

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
        "imagenes": [
            {
                "id_imagen": img.id_imagen,
                "url_foto": img.url_foto,
                "is_portada": img.numero_imagen == 1,  # True si es la primera imagen
                "numero_imagen": img.numero_imagen
            } for img in imagenes
        ] if imagenes else []
    }


# --- PUT: actualizar publicación ---
@router.put("/{id}")
async def actualizar_publicacion(
    id: int,
    titulo: str = Form(...),
    descripcion_corta: str = Form(...),
    descripcion: str = Form(...),
    detalle: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    year_vehiculo: int = Form(...),
    id_categoria_vehiculo: int = Form(...),
    id_marca_vehiculo: int = Form(...),
    mantener_imagenes: str = Form(""),
    nueva_portada: Optional[str] = Form(None),
    files: List[UploadFile] = [],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # --- Validación de propiedad ---
        publicacion = db.query(Publicacion).filter(Publicacion.id_publicacion == id).first()
        if not publicacion:
            raise HTTPException(status_code=404, detail="Publicación no encontrada")
        if publicacion.id_usuario != current_user["id"]:
            raise HTTPException(status_code=403, detail="No tienes permiso para editar esta publicación")

        # --- Actualizar campos de la publicación ---
        publicacion.titulo = titulo
        publicacion.descripcion_corta = descripcion_corta
        publicacion.descripcion = descripcion
        publicacion.detalle = detalle
        publicacion.url = url
        publicacion.year_vehiculo = year_vehiculo
        publicacion.id_categoria_vehiculo = id_categoria_vehiculo
        publicacion.id_marca_vehiculo = id_marca_vehiculo
        db.add(publicacion)

        # --- Manejo de imágenes ---
        # Mantener imágenes existentes
        keep_ids = []
        if mantener_imagenes:
            keep_ids = [int(x.strip()) for x in mantener_imagenes.split(',') if x.strip()]
            # Eliminar las que no se mantienen
            db.query(Imagen).filter(
                Imagen.id_publicacion == id,
                ~Imagen.id_imagen.in_(keep_ids)
            ).delete(synchronize_session=False)
        else:
            # Si no mantiene ninguna, eliminar todas
            db.query(Imagen).filter(Imagen.id_publicacion == id).delete(synchronize_session=False)

        # Obtener todas las imágenes que quedan (mantenidas + nuevas que se agregarán)
        imagenes_existentes = (
            db.query(Imagen)
            .filter(Imagen.id_publicacion == id)
            .order_by(Imagen.numero_imagen)
            .all()
        )

        # Agregar nuevas imágenes
        nueva_imagen_objs = []
        siguiente_numero = len(imagenes_existentes) + 1
        
        for i, file in enumerate(files):
            file_url = upload_to_gcs(file)
            nueva_img = Imagen(
                id_publicacion=id,
                url_foto=file_url,
                numero_imagen=siguiente_numero + i
            )
            db.add(nueva_img)
            db.flush()  # Para obtener id_imagen
            nueva_imagen_objs.append(nueva_img)

        # --- Lógica para definir la nueva portada ---
        # Obtener todas las imágenes actuales (existentes + nuevas)
        todas_imagenes = imagenes_existentes + nueva_imagen_objs
        
        # Determinar qué imagen debe ser la portada
        portada_objetivo = None
        
        if nueva_portada:
            if nueva_portada.startswith("nueva_"):
                # Es una imagen nueva
                index = int(nueva_portada.split("_")[1])
                if index < len(nueva_imagen_objs):
                    portada_objetivo = nueva_imagen_objs[index]
            elif nueva_portada.isdigit():
                # Es una imagen existente
                pid = int(nueva_portada)
                portada_objetivo = next((img for img in imagenes_existentes if img.id_imagen == pid), None)
        
        # Si no se especificó portada, la primera imagen será la portada
        if not portada_objetivo and todas_imagenes:
            portada_objetivo = todas_imagenes[0]

        # --- Reorganizar números para que la portada sea número 1 ---
        if portada_objetivo:
            # Lista de todas las imágenes ordenadas: portada primero, luego el resto
            imagenes_ordenadas = [portada_objetivo]
            for img in todas_imagenes:
                if img.id_imagen != portada_objetivo.id_imagen:
                    imagenes_ordenadas.append(img)
            
            # Reasignar números secuenciales
            for idx, img in enumerate(imagenes_ordenadas, start=1):
                img.numero_imagen = idx

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

        # Obtener imágenes asociadas (ordenadas por numero_imagen)
        imagenes = (
            db.query(Imagen)
            .filter(Imagen.id_publicacion == id_publicacion)
            .order_by(Imagen.numero_imagen)
            .all()
        )

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


# --- Endpoint para reordenar imágenes ---
@router.put("/{id_publicacion}/reorder-images")
async def reordenar_imagenes(
    id_publicacion: int,
    nuevos_numeros: List[dict],  # [{"id_imagen": 1, "numero_imagen": 2}, ...]
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Permite reordenar las imágenes de una publicación actualizando numero_imagen.
    La imagen con numero_imagen = 1 será automáticamente la portada.
    
    Args:
        nuevos_numeros: Lista de objetos con id_imagen y su nuevo numero_imagen
    """
    try:
        # Verificar propiedad de la publicación
        publicacion = db.query(Publicacion).filter(Publicacion.id_publicacion == id_publicacion).first()
        if not publicacion:
            raise HTTPException(status_code=404, detail="Publicación no encontrada")
        if publicacion.id_usuario != current_user["id"]:
            raise HTTPException(status_code=403, detail="No tienes permiso para editar esta publicación")

        # Actualizar los números de imagen
        for item in nuevos_numeros:
            db.query(Imagen).filter(
                Imagen.id_imagen == item["id_imagen"],
                Imagen.id_publicacion == id_publicacion
            ).update({Imagen.numero_imagen: item["numero_imagen"]})

        db.commit()
        return {"mensaje": "Orden de imágenes actualizado correctamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error reordenando imágenes: {str(e)}")
