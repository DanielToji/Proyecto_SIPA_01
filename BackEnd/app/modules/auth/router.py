from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import random

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.models import Usuario, Rol
from app.modules.auth import schemas, services
from app.modules.auth.crud import get_usuario_by_email, update_password

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================
# LOGIN
# ============================================================
@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = get_usuario_by_email(db, credentials.email)
    if not usuario or not usuario.is_active or not verify_password(credentials.password, usuario.password_hash):
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
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "rol_id": usuario.rol_id,
        "usuario_id": usuario.id,
        "nombre": f"{usuario.nombre} {usuario.apellido}",
    }


# ============================================================
# REGISTRO
# ============================================================
@router.post("/register", response_model=schemas.UserInfoResponse, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Usuario).filter(Usuario.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    if data.documento_identidad:
        existing_doc = db.query(Usuario).filter(
            Usuario.documento_identidad == data.documento_identidad
        ).first()
        if existing_doc:
            raise HTTPException(status_code=400, detail="El documento ya está registrado")

    new_user = Usuario(
        nombre=data.nombre,
        apellido=data.apellido,
        email=data.email,
        password_hash=get_password_hash(data.password),
        tipo_documento=data.tipo_documento,
        documento_identidad=data.documento_identidad,
        telefono=data.telefono,
        rol_id=data.rol_id if data.rol_id else 4
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    rol = db.query(Rol).filter(Rol.id == new_user.rol_id).first()

    return schemas.UserInfoResponse(
        id=new_user.id,
        nombre=new_user.nombre,
        apellido=new_user.apellido,
        email=new_user.email,
        rol_id=new_user.rol_id,
        tipo_documento=new_user.tipo_documento,
        documento_identidad=new_user.documento_identidad,
        telefono=new_user.telefono,
        is_active=new_user.is_active
    )


# ============================================================
# USUARIO ACTUAL
# ============================================================
@router.get("/me", response_model=schemas.UsuarioMe)
def obtener_usuario_actual(current_user: Usuario = Depends(get_current_user)):
    return current_user


# ============================================================
# CAMBIAR CONTRASEÑA (autenticado)
# ============================================================
@router.post("/cambiar-password")
@limiter.limit("5/minute")
def cambiar_password(
    request: Request,
    datos: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not verify_password(datos.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")

    new_hash = get_password_hash(datos.new_password)
    update_password(db, current_user, new_hash)
    return {"mensaje": "Contraseña actualizada correctamente"}


# ============================================================
# PASO 1: SOLICITAR CÓDIGO DE 6 DÍGITOS
# ============================================================
@router.post("/recuperar-password", response_model=schemas.PasswordResetRequestResponse)
@limiter.limit("3/minute")
def solicitar_recuperacion(
    request: Request,
    datos: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Solicita un código de 6 dígitos para recuperar contraseña.
    En DEBUG, el código se devuelve en la respuesta.
    En producción, se envía por email.
    """
    usuario = get_usuario_by_email(db, datos.email)

    if usuario and usuario.is_active:
        reset_code = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        usuario.reset_code = reset_code
        usuario.reset_code_expires_at = expires_at
        db.commit()

        # Log en consola del backend
        print("\n" + "=" * 60)
        print("📧 CÓDIGO DE RECUPERACIÓN GENERADO")
        print(f"   Email:  {usuario.email}")
        print(f"   Código: {reset_code}")
        print(f"   Expira: {expires_at} UTC")
        print("=" * 60 + "\n")

        # Enviar por email si el servicio está disponible
        try:
            services.send_password_reset_code(usuario.email, reset_code)
        except Exception as e:
            print(f"⚠️  Email no enviado: {e}")

        # ⚠️ En DEBUG devolvemos el código para poder probarlo
        if settings.DEBUG:
            return schemas.PasswordResetRequestResponse(
                mensaje="Código generado (modo DEBUG)",
                codigo=reset_code,
                expira_en_minutos=15
            )

    # Respuesta genérica (no revelar si el email existe)
    return schemas.PasswordResetRequestResponse(
        mensaje="Si el correo existe, se ha enviado un código de recuperación"
    )


# ============================================================
# PASO 2: VERIFICAR CÓDIGO
# ============================================================
@router.post("/verificar-codigo")
@limiter.limit("5/minute")
def verificar_codigo(
    request: Request,
    datos: schemas.VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    usuario = get_usuario_by_email(db, datos.email)

    if not usuario:
        raise HTTPException(status_code=400, detail="Código inválido")

    if usuario.reset_code != datos.code:
        raise HTTPException(status_code=400, detail="Código incorrecto")

    if not usuario.reset_code_expires_at or usuario.reset_code_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código expirado")

    return {"mensaje": "Código válido", "valido": True}


# ============================================================
# PASO 3: RESTABLECER CONTRASEÑA
# ============================================================
@router.post("/restablecer-password")
@limiter.limit("5/minute")
def confirmar_recuperacion(
    request: Request,
    datos: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    usuario = get_usuario_by_email(db, datos.email)

    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if usuario.reset_code != datos.code:
        raise HTTPException(status_code=400, detail="Código incorrecto")

    if not usuario.reset_code_expires_at or usuario.reset_code_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código expirado")

    new_hash = get_password_hash(datos.new_password)
    usuario.password_hash = new_hash
    usuario.reset_code = None
    usuario.reset_code_expires_at = None
    db.commit()

    print(f"\n CONTRASEÑA RESTABLECIDA PARA: {usuario.email}\n")

    return {"mensaje": "Contraseña restablecida correctamente"}