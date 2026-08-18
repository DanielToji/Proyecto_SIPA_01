from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import TipoCharla


# ================== Charla ==================
class CharlaBase(BaseModel):
    ficha_id: int
    tipo_charla: TipoCharla
    fecha_programada: datetime
    instructor_id: int
    tema: Optional[str] = Field(None, max_length=200)


class CharlaCreate(CharlaBase):
    pass


class CharlaUpdate(BaseModel):
    ficha_id: Optional[int] = None
    tipo_charla: Optional[TipoCharla] = None
    fecha_programada: Optional[datetime] = None
    instructor_id: Optional[int] = None
    tema: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class CharlaOut(CharlaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ================== Asistencia ==================
class AsistenciaCharlaItem(BaseModel):
    aprendiz_id: int
    asistio: bool = False
    fecha_asistencia: Optional[date] = None
    evidencia_archivo_id: Optional[int] = None
    observaciones: Optional[str] = Field(None, max_length=500)


class AsistenciaCharlaCreate(BaseModel):
    asistencias: List[AsistenciaCharlaItem] = Field(..., min_items=1)

    @model_validator(mode="after")
    def validar_sin_duplicados(self):
        ids = [item.aprendiz_id for item in self.asistencias]
        if len(ids) != len(set(ids)):
            raise ValueError("No se permiten aprendices duplicados en la lista de asistencias")
        return self


class AsistenciaCharlaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    charla_id: int
    aprendiz_id: int
    asistio: bool
    fecha_asistencia: Optional[date]
    evidencia_archivo_id: Optional[int]
    observaciones: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime