from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import TipoDocumento
from app.modules.auth.schemas import validar_fortaleza_password


# ================== Rol ==================
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


# ================== Usuario ==================
class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    tipo_documento: Optional[TipoDocumento] = None
    documento_identidad: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=20)
    rol_id: int


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        return validar_fortaleza_password(v)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    tipo_documento: Optional[TipoDocumento] = None
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
    tipo_documento: Optional[TipoDocumento]
    documento_identidad: Optional[str]
    telefono: Optional[str]
    rol_id: int
    is_active: bool
    preferencias_ui: dict
    created_at: datetime
    updated_at: datetime


class PreferenciasUpdate(BaseModel):
    preferencias_ui: dict