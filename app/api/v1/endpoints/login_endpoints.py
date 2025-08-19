from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.db.database import get_db
from app.db.models import Usuario
from app.core.security import verify_password, create_access_token, decode_token

router = APIRouter()

@router.post("/login")

def login(
    response: Response,  # Para modificar la respuesta y añadir cookies
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.nombre_usuario == form_data.username).first()

    if not usuario or not verify_password(form_data.password, usuario.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": usuario.nombre_usuario})

    # Imprimir el token en consola backend para verificar
    print("Access token generado en backend:", access_token)

    # Aquí seteamos la cookie httpOnly
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Cambiar a True en producción con HTTPS
        samesite="none",
        max_age=60*60*2,  # ⏱️ 2 horas por ejemplo
    )

    return {"msg": "Login exitoso"}

@router.get("/me")
def me(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")

    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    usuario_nombre = payload.get("sub")
    if not usuario_nombre:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    return {"usuario": {"nombre": usuario_nombre}}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"msg": "Sesión cerrada"}
