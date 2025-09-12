from fastapi import APIRouter, Depends, UploadFile, HTTPException, Form, status, File, Query
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

router = APIRouter()
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


@router.get("/edit-post/{id_publicacion}", response_model=PublicacionEditDetails)
async def obtener_publicacion_para_editar(
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
    
    # 3️⃣ Todas las imágenes - MODIFICADO PARA INCLUIR IDs
    imagenes = (
        db.query(Imagen)
        .filter(Imagen.id_publicacion == publicacion.id_publicacion)
        .order_by(Imagen.id_imagen)  # Ordenar por ID para consistencia
        .all()
    )
    
    # 4️⃣ Devolver resultado - CAMBIO PRINCIPAL AQUÍ
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
                "is_portada": img.imagen_portada == b'\x01'
            }
            for img in imagenes
        ] if imagenes else []
    }

def delete_from_gcs(file_url: str) -> bool:
    """
    Elimina un archivo de Google Cloud Storage usando su URL.
    
    Args:
        file_url (str): URL completa del archivo en GCS
        
    Returns:
        bool: True si se eliminó correctamente, False si hubo error
    """
    try:
        # Configurar cliente de GCS
        client = storage.Client()
        
        # Extraer el nombre del bucket y el blob name de la URL
        # Ejemplo: https://storage.googleapis.com/tu-bucket/carpeta/archivo.jpg
        parsed_url = urlparse(file_url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)
        
        if len(path_parts) < 2:
            print(f"URL inválida: {file_url}")
            return False
            
        bucket_name = path_parts[0]
        blob_name = path_parts[1]
        
        # Obtener el bucket
        bucket = client.bucket(bucket_name)
        
        # Obtener el blob (archivo)
        blob = bucket.blob(blob_name)
        
        # Eliminar el archivo
        blob.delete()
        
        print(f"Archivo eliminado exitosamente: {blob_name}")
        return True
        
    except NotFound:
        print(f"Archivo no encontrado en GCS: {file_url}")
        return False
    except Exception as e:
        print(f"Error eliminando archivo de GCS: {str(e)}")
        return False

@router.delete("/{id_publicacion}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_publicacion(
    id_publicacion: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una publicación. Solo el propietario puede eliminar su publicación.
    También elimina todas las imágenes asociadas.
    """
    try:
        # Buscar la publicación
        pub = db.query(Publicacion).filter(
            Publicacion.id_publicacion == id_publicacion
        ).first()
        
        if not pub:
            raise HTTPException(status_code=404, detail="Publicación no encontrada")
        
        # Verificar que el usuario sea el propietario
        if pub.id_usuario != current_user["id"]:
            raise HTTPException(
                status_code=403, 
                detail="No tienes permiso para eliminar esta publicación"
            )
        
        # Obtener y eliminar imágenes asociadas
        imagenes = db.query(Imagen).filter(
            Imagen.id_publicacion == id_publicacion
        ).all()
        
        # Eliminar archivos de GCS y registros de BD
        for img in imagenes:
            # Eliminar archivo físico de Google Cloud Storage
            try:
                delete_success = delete_from_gcs(img.url_foto)
                if not delete_success:
                    print(f"Advertencia: No se pudo eliminar {img.url_foto} de GCS")
            except Exception as e:
                print(f"Error eliminando imagen de GCS: {e}")
                # Continuar con la eliminación de la BD aunque falle GCS
            
            # Eliminar registro de la base de datos
            db.delete(img)
        
        # Eliminar la publicación
        db.delete(pub)
        db.commit()
        
        return  # 204 No Content no devuelve body
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )
    

# BACKEND (Python/FastAPI) - Actualizar tu endpoint PUT

@app.put("/api/v1/publicacion/{id}")
async def actualizar_publicacion(id: int, request: Request):
    try:
        form = await request.form()
        nueva_portada = form.get('nueva_portada')
        mantener_imagenes = form.get('mantener_imagenes', '')
        files = form.getlist('files')
        
        # ... resto de tu lógica para actualizar la publicación ...
        
        # NUEVA LÓGICA PARA MANEJAR LA PORTADA SIN DUPLICACIÓN
        
        # 1. PRIMERO: Quitar portada de TODAS las imágenes existentes de esta publicación
        await db.execute(
            "UPDATE imagenes SET is_portada = FALSE WHERE id_publicacion = ?", 
            [id]
        )
        
        # 2. Procesar imágenes que se mantienen
        keep_ids = []
        if mantener_imagenes:
            keep_ids = [int(x.strip()) for x in mantener_imagenes.split(',') if x.strip()]
            
            # Eliminar imágenes que NO se van a mantener
            if keep_ids:
                placeholders = ','.join(['?' for _ in keep_ids])
                await db.execute(
                    f"DELETE FROM imagenes WHERE id_publicacion = ? AND id_imagen NOT IN ({placeholders})",
                    [id] + keep_ids
                )
        else:
            # Si no se mantiene ninguna imagen, eliminar todas
            await db.execute("DELETE FROM imagenes WHERE id_publicacion = ?", [id])
        
        # 3. Insertar nuevas imágenes
        nueva_imagen_ids = []
        for i, file in enumerate(files):
            # Guardar archivo y obtener URL
            file_url = await save_image_file(file)  # Tu función para guardar imágenes
            
            # Insertar nueva imagen
            result = await db.execute(
                "INSERT INTO imagenes (id_publicacion, url_foto, is_portada) VALUES (?, ?, ?)",
                [id, file_url, False]  # Inicialmente todas como NO portada
            )
            nueva_imagen_ids.append(result.lastrowid)
        
        # 4. ESTABLECER LA PORTADA SEGÚN LA LÓGICA ENVIADA DESDE EL FRONTEND
        if nueva_portada:
            if nueva_portada == 'nueva_0' and nueva_imagen_ids:
                # La primera nueva imagen será la portada
                await db.execute(
                    "UPDATE imagenes SET is_portada = TRUE WHERE id_imagen = ?",
                    [nueva_imagen_ids[0]]
                )
            elif nueva_portada != 'nueva_0' and nueva_portada.isdigit():
                # Una imagen existente que se mantuvo será la portada
                image_id = int(nueva_portada)
                if image_id in keep_ids:  # Verificar que la imagen se mantuvo
                    await db.execute(
                        "UPDATE imagenes SET is_portada = TRUE WHERE id_imagen = ?",
                        [image_id]
                    )
        else:
            # Fallback: Si no se especifica portada, la primera imagen disponible será portada
            if keep_ids:
                await db.execute(
                    "UPDATE imagenes SET is_portada = TRUE WHERE id_imagen = ? LIMIT 1",
                    [keep_ids[0]]
                )
            elif nueva_imagen_ids:
                await db.execute(
                    "UPDATE imagenes SET is_portada = TRUE WHERE id_imagen = ? LIMIT 1",
                    [nueva_imagen_ids[0]]
                )
        
        # 5. VERIFICACIÓN FINAL: Asegurar que solo hay UNA portada
        portada_count = await db.fetch_val(
            "SELECT COUNT(*) FROM imagenes WHERE id_publicacion = ? AND is_portada = TRUE",
            [id]
        )
        
        if portada_count == 0:
            # Si no hay portada, hacer portada a la primera imagen disponible
            first_image = await db.fetch_one(
                "SELECT id_imagen FROM imagenes WHERE id_publicacion = ? ORDER BY id_imagen LIMIT 1",
                [id]
            )
            if first_image:
                await db.execute(
                    "UPDATE imagenes SET is_portada = TRUE WHERE id_imagen = ?",
                    [first_image['id_imagen']]
                )
        elif portada_count > 1:
            # Si hay múltiples portadas, mantener solo la primera
            portadas = await db.fetch_all(
                "SELECT id_imagen FROM imagenes WHERE id_publicacion = ? AND is_portada = TRUE ORDER BY id_imagen",
                [id]
            )
            
            # Mantener solo la primera como portada
            for i, portada in enumerate(portadas):
                if i > 0:  # Quitar portada de las demás
                    await db.execute(
                        "UPDATE imagenes SET is_portada = FALSE WHERE id_imagen = ?",
                        [portada['id_imagen']]
                    )
        
        await db.commit()
        
        return {"mensaje": "Publicación actualizada correctamente", "id": id}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando publicación: {str(e)}")


# FUNCIÓN HELPER PARA GUARDAR IMÁGENES (si no la tienes)
async def save_image_file(file):
    """
    Guarda el archivo de imagen y retorna la URL
    """
    import os
    import uuid
    from pathlib import Path
    
    # Generar nombre único para el archivo
    file_extension = file.filename.split('.')[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Crear directorio si no existe
    upload_dir = Path("uploads/images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar archivo
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Retornar URL relativa o absoluta según tu configuración
    return f"/uploads/images/{unique_filename}"
