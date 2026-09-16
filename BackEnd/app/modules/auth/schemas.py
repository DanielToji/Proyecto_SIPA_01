from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

# ============================================================
# Esquemas de Autenticación
# ============================================================

class LoginRequest(BaseModel):
    """Solicitud de login"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Respuesta con token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    rol_id: int
    usuario_id: int
    nombre: str

class UserInfoResponse(BaseModel):
    """Información del usuario autenticado"""
    id: int
    nombre: str
    apellido: str
    email: str
    rol_id: int
    tipo_documento: Optional[str] = None
    documento_identidad: Optional[str] = None
    telefono: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class RegisterRequest(BaseModel):
    """Solicitud de registro de usuario"""
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    tipo_documento: Optional[str] = None
    documento_identidad: Optional[str] = None
    telefono: Optional[str] = None
    rol_id: int = 4  # Aprendiz por defecto

class PasswordChange(BaseModel):
    """Cambio de contraseña"""
    old_password: str
    new_password: str = Field(..., min_length=6)

class UsuarioMe(BaseModel):
    """Información del usuario para el endpoint /me"""
    id: int
    nombre: str
    apellido: str
    email: str
    rol_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================
# ESQUEMAS DE RECUPERACIÓN DE CONTRASEÑA (CON CÓDIGO DE 6 DÍGITOS)
# ============================================================

class PasswordResetRequest(BaseModel):
    """Solicitud de recuperación - Solo email"""
    email: EmailStr


class PasswordResetRequestResponse(BaseModel):
    """🔥 NUEVO - Respuesta del paso 1.
    En modo DEBUG incluye el código para pruebas."""
    mensaje: str
    codigo: Optional[str] = None
    expira_en_minutos: Optional[int] = None


class VerifyCodeRequest(BaseModel):
    """Verificación de código de 6 dígitos"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def code_solo_digitos(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El código debe contener solo dígitos")
        return v


class PasswordResetConfirm(BaseModel):
    """Confirmación con código de 6 dígitos"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)

    @field_validator("code")
    @classmethod
    def code_solo_digitos(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El código debe contener solo dígitos")
        return v