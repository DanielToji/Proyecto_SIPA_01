from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional
from datetime import datetime
import re

# ============================================================
# FUNCIÓN DE VALIDACIÓN DE CONTRASEÑA
# ============================================================

def validar_fortaleza_password(password: str) -> str:
    """
    Valida que la contraseña cumpla con los requisitos de seguridad:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    
    if not re.search(r'[A-Z]', password):
        raise ValueError("La contraseña debe tener al menos una mayúscula")
    
    if not re.search(r'[a-z]', password):
        raise ValueError("La contraseña debe tener al menos una minúscula")
    
    if not re.search(r'\d', password):
        raise ValueError("La contraseña debe tener al menos un número")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("La contraseña debe tener al menos un carácter especial")
    
    return password


# ============================================================
# ESQUEMAS DE ROLES
# ============================================================

class RolBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=50, description="Nombre único del rol")
    descripcion: Optional[str] = Field(None, max_length=255)


class RolCreate(RolBase):
    pass


class RolUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class RolOut(RolBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================
# ESQUEMAS DE USUARIOS
# ============================================================

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    tipo_documento: Optional[str] = None
    documento_identidad: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=20)
    rol_id: int


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        return validar_fortaleza_password(v)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    tipo_documento: Optional[str] = None
    documento_identidad: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=20)
    rol_id: Optional[int] = None
    is_active: Optional[bool] = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    tipo_documento: Optional[str] = None
    documento_identidad: Optional[str] = None
    telefono: Optional[str] = None
    rol_id: int
    is_active: bool
    preferencias_ui: dict = {}
    created_at: datetime
    updated_at: datetime


class PreferenciasUpdate(BaseModel):
    preferencias_ui: dict


class UsuarioFilter(BaseModel):
    search: Optional[str] = None
    rol_id: Optional[int] = None
    is_active: Optional[bool] = True
    skip: int = 0
    limit: int = 100


class UsuarioListResponse(BaseModel):
    total: int
    items: list[UsuarioOut]