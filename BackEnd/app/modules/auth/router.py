from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.models import Usuario
from app.modules.auth import crud, schemas, services

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica al usuario y retorna un token JWT con su rol principal.
    RF-01: Autenticación de usuarios con permisos según rol.
    """
    usuario = crud.get_usuario_by_email(db, credentials.email)
    if not usuario or not usuario.is_active or not verify_password(credentials.password, usuario.password_hash):
        # Mensaje genérico para no revelar si el correo existe o si está inactivo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    access_token = create_access_token(
        data={
            "sub": str(usuario.id),
            "rol": usuario.rol_id,
            "nombre": f"{usuario.nombre} {usuario.apellido}"
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "rol_id": usuario.rol_id,
        "usuario_id": usuario.id,
        "nombre": f"{usuario.nombre} {usuario.apellido}",
    }


@router.get("/me", response_model=schemas.UsuarioMe)
def obtener_usuario_actual(current_user: Usuario = Depends(get_current_user)):
    """
    Retorna la información del usuario autenticado.
    """
    return current_user


@router.post("/cambiar-password")
@limiter.limit("5/minute")
def cambiar_password(
    request: Request,
    datos: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite al usuario autenticado cambiar su contraseña.
    Valida la contraseña actual antes de actualizar.
    """
    if not verify_password(datos.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")

    new_hash = get_password_hash(datos.new_password)
    crud.update_password(db, current_user, new_hash)
    return {"mensaje": "Contraseña actualizada correctamente"}


@router.post("/recuperar-password")
@limiter.limit("3/minute")
def solicitar_recuperacion(
    request: Request,
    datos: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Solicita un enlace de recuperación de contraseña.
    Envía un correo con enlace de un solo uso si el usuario existe y está activo.
    Siempre retorna el mismo mensaje para evitar enumeración de usuarios.
    """
    usuario = crud.get_usuario_by_email(db, datos.email)
    if usuario and usuario.is_active:
        # Generar token JWT de recuperación con expiración corta
        expire = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        token = jwt.encode(
            {
                "sub": str(usuario.id),
                "type": "password_reset",
                "iat": datetime.utcnow(),
                "exp": expire,
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        reset_link = f"{settings.FRONTEND_URL}/restablecer-password?token={token}"
        try:
            services.send_password_reset_email(usuario.email, reset_link)
        except Exception:
            # No exponer error interno ni dar pistas de si el usuario existe
            raise HTTPException(status_code=500, detail="Error al enviar el correo de recuperación")

    # Respuesta idéntica exista o no el usuario
    return {"mensaje": "Si el correo existe, se ha enviado un enlace de recuperación"}


@router.post("/restablecer-password")
@limiter.limit("5/minute")
def confirmar_recuperacion(
    request: Request,
    datos: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Restablece la contraseña usando un token de recuperación válido.
    El token debe ser de tipo `password_reset` y no estar expirado.
    """
    try:
        payload = jwt.decode(
            datos.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "password_reset":
            raise JWTError("Token no es de recuperación")
        usuario_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    usuario = crud.get_usuario_by_id(db, usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o inactivo")

    new_hash = get_password_hash(datos.new_password)
    crud.update_password(db, usuario, new_hash)
    return {"mensaje": "Contraseña restablecida correctamente"}