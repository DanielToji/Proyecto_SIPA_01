from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


def validar_fortaleza_password(password: str) -> str:
    """Valida que la contraseña cumpla requisitos mínimos de seguridad."""
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not any(c.isupper() for c in password):
        raise ValueError("La contraseña debe contener al menos una mayúscula")
    if not any(c.islower() for c in password):
        raise ValueError("La contraseña debe contener al menos una minúscula")
    if not any(c.isdigit() for c in password):
        raise ValueError("La contraseña debe contener al menos un número")
    if not any(c in "!@#$%^&*()-_=+[]{};:,.<>?/" for c in password):
        raise ValueError("La contraseña debe contener al menos un carácter especial")
    return password


class LoginRequest(BaseModel):
    """Credenciales de acceso."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Respuesta al autenticarse correctamente."""
    access_token: str
    token_type: str = "bearer"
    rol_id: int
    usuario_id: int
    nombre: str


class UsuarioMe(BaseModel):
    """Información del usuario autenticado."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
    email: EmailStr
    rol_id: int
    tipo_documento: Optional[str]
    documento_identidad: Optional[str]
    telefono: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PasswordChange(BaseModel):
    """Cambio de contraseña estando autenticado."""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(...)

    @field_validator("new_password")
    @classmethod
    def validar_new_password(cls, v: str) -> str:
        return validar_fortaleza_password(v)


class PasswordResetRequest(BaseModel):
    """Solicitud de enlace de recuperación."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirmación de recuperación con token y nueva contraseña."""
    token: str = Field(..., min_length=20, description="Token JWT de recuperación")
    new_password: str = Field(...)

    @field_validator("new_password")
    @classmethod
    def validar_new_password(cls, v: str) -> str:
        return validar_fortaleza_password(v)