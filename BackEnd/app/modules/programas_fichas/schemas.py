from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoAsignacion


# ================== Programa de Formación ==================
class ProgramaFormacionBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=30, description="Código único del programa")
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)


class ProgramaFormacionCreate(ProgramaFormacionBase):
    pass


class ProgramaFormacionUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=2, max_length=30)
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ProgramaFormacionOut(ProgramaFormacionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ================== Ficha ==================
class FichaBase(BaseModel):
    programa_id: int
    numero_ficha: str = Field(..., min_length=3, max_length=20)
    fecha_inicio: date
    fecha_fin: date


class FichaCreate(FichaBase):
    pass


class FichaUpdate(BaseModel):
    programa_id: Optional[int] = None
    numero_ficha: Optional[str] = Field(None, min_length=3, max_length=20)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    is_active: Optional[bool] = None


class FichaOut(FichaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ================== Asignación Instructor-Ficha ==================
class AsignacionInstructorFichaBase(BaseModel):
    ficha_id: int
    instructor_id: int


class AsignacionInstructorFichaCreate(AsignacionInstructorFichaBase):
    pass


class AsignacionInstructorFichaUpdate(BaseModel):
    estado_asignacion: Optional[EstadoAsignacion] = None
    is_active: Optional[bool] = None


class AsignacionInstructorFichaOut(AsignacionInstructorFichaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_asignacion: date
    estado_asignacion: EstadoAsignacion
    is_active: bool
    created_at: datetime
    updated_at: datetime