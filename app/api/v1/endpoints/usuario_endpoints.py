from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.core.security import hash_password, get_current_user

router = APIRouter()


def _require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("tipo_usuario") != "0":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return current_user


@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def create_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.nombre_usuario == usuario.nombre_usuario).first()
    if existe:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    nuevo = Usuario(
        nombre_usuario=usuario.nombre_usuario,
        password=hash_password(usuario.password),
        tipo_usuario="1",  # Siempre usuario normal; el rol admin se asigna manualmente en BD
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/", response_model=List[UsuarioOut])
def get_all_usuarios(
    db: Session = Depends(get_db),
    current_user: dict = Depends(_require_admin)
):
    return db.query(Usuario).all()


@router.get("/{usuario_id}", response_model=UsuarioOut)
def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["id"] != usuario_id and current_user.get("tipo_usuario") != "0":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioOut)
def update_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["id"] != usuario_id and current_user.get("tipo_usuario") != "0":
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este usuario")

    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = usuario_data.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    for key, value in update_data.items():
        setattr(usuario, key, value)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["id"] != usuario_id and current_user.get("tipo_usuario") != "0":
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este usuario")

    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
