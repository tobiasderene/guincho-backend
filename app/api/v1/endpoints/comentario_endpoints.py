from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Comentario, Usuario
from app.schemas.comentarios import ComentarioCreate, ComentarioOut
from app.core.security import get_current_user

router = APIRouter()


@router.post("/", response_model=ComentarioOut, status_code=status.HTTP_201_CREATED)
def crear_comentario(
    comentario: ComentarioCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    nuevo_comentario = Comentario(
        descripcion_comentario=comentario.descripcion_comentario,
        id_usuario=current_user["id"],
        id_publicacion=comentario.id_publicacion
    )
    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)

    usuario = db.query(Usuario).filter(Usuario.id_usuario == nuevo_comentario.id_usuario).first()

    response = ComentarioOut.from_orm(nuevo_comentario)
    response.nombre_usuario = usuario.nombre_usuario if usuario else f"Usuario {nuevo_comentario.id_usuario}"
    response.fecha_comentario = "hace un momento"

    return response


@router.get("/", response_model=List[ComentarioOut])
def obtener_comentarios(db: Session = Depends(get_db)):
    comentarios = (
        db.query(Comentario, Usuario.nombre_usuario)
        .join(Usuario, Comentario.id_usuario == Usuario.id_usuario)
        .all()
    )

    result = []
    for comentario, nombre_usuario in comentarios:
        comment_dict = ComentarioOut.from_orm(comentario).dict()
        comment_dict['nombre_usuario'] = nombre_usuario
        comment_dict['fecha_comentario'] = "Sin fecha"
        result.append(ComentarioOut(**comment_dict))

    return result


@router.get("/publicacion/{id_publicacion}", response_model=List[ComentarioOut])
def obtener_comentarios_por_publicacion(id_publicacion: int, db: Session = Depends(get_db)):
    comentarios = (
        db.query(Comentario, Usuario.nombre_usuario)
        .join(Usuario, Comentario.id_usuario == Usuario.id_usuario)
        .filter(Comentario.id_publicacion == id_publicacion)
        .all()
    )

    result = []
    for comentario, nombre_usuario in comentarios:
        comment_dict = ComentarioOut.from_orm(comentario).dict()
        comment_dict['nombre_usuario'] = nombre_usuario
        comment_dict['fecha_comentario'] = "Sin fecha"
        result.append(ComentarioOut(**comment_dict))

    return result


@router.delete("/{id_comentario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_comentario(
    id_comentario: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    comentario = db.query(Comentario).filter(Comentario.id_comentario == id_comentario).first()
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")

    if comentario.id_usuario != current_user["id"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este comentario")

    db.delete(comentario)
    db.commit()
