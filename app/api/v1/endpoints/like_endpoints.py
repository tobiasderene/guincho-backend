from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Like
from app.schemas.likes import LikesCreate, LikesOut
from app.core.security import get_current_user

router = APIRouter()


@router.post("/", response_model=LikesOut, status_code=status.HTTP_201_CREATED)
def dar_like(
    like: LikesCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if (like.id_comentario is None and like.id_publicacion is None) or \
       (like.id_comentario is not None and like.id_publicacion is not None):
        raise HTTPException(
            status_code=400,
            detail="Debe especificar solo un tipo de like: comentario o publicación"
        )

    ya_existe = db.query(Like).filter(
        Like.id_usuario == current_user["id"],
        Like.id_comentario == like.id_comentario,
        Like.id_publicacion == like.id_publicacion
    ).first()

    if ya_existe:
        raise HTTPException(status_code=400, detail="Ya diste like")

    nuevo_like = Like(
        id_usuario=current_user["id"],
        id_comentario=like.id_comentario,
        id_publicacion=like.id_publicacion
    )
    db.add(nuevo_like)
    db.commit()
    db.refresh(nuevo_like)
    return nuevo_like


@router.get("/", response_model=List[LikesOut])
def obtener_likes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(Like).filter(Like.id_usuario == current_user["id"]).all()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def quitar_like(
    like: LikesCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    like_db = db.query(Like).filter(
        Like.id_usuario == current_user["id"],
        Like.id_comentario == like.id_comentario,
        Like.id_publicacion == like.id_publicacion
    ).first()

    if not like_db:
        raise HTTPException(status_code=404, detail="Like no encontrado")

    db.delete(like_db)
    db.commit()
