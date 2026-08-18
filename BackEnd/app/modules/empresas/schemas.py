from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ================== Empresa ==================
class EmpresaBase(BaseModel):
    nit: str = Field(..., min_length=5, max_length=20, description="NIT de la empresa")
    razon_social: str = Field(..., min_length=3, max_length=200)
    direccion: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=20)
    correo_contacto: Optional[EmailStr] = None


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    nit: Optional[str] = Field(None, min_length=5, max_length=20)
    razon_social: Optional[str] = Field(None, min_length=3, max_length=200)
    direccion: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=20)
    correo_contacto: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ================== Coordinador de Empresa ==================
class CoordinadorEmpresaBase(BaseModel):
    empresa_id: int
    nombre: str = Field(..., min_length=3, max_length=150)
    cargo: Optional[str] = Field(None, max_length=100)
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)


class CoordinadorEmpresaCreate(CoordinadorEmpresaBase):
    pass


class CoordinadorEmpresaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=150)
    cargo: Optional[str] = Field(None, max_length=100)
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class CoordinadorEmpresaOut(CoordinadorEmpresaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime