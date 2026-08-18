from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import MomentoReunion


class ReunionSeguimientoBase(BaseModel):
    proceso_id: int
    momento: MomentoReunion
    fecha_programada: datetime
    instructor_id: int
    observaciones: Optional[str] = Field(None, max_length=1000)


class ReunionSeguimientoCreate(ReunionSeguimientoBase):
    pass


class ReunionSeguimientoUpdate(BaseModel):
    fecha_programada: Optional[datetime] = None
    fecha_realizada: Optional[datetime] = None
    instructor_id: Optional[int] = None
    observaciones: Optional[str] = Field(None, max_length=1000)
    evidencia_archivo_id: Optional[int] = None
    archivo_f023_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ReunionSeguimientoOut(ReunionSeguimientoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_realizada: Optional[datetime]
    evidencia_archivo_id: Optional[int]
    archivo_f023_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime