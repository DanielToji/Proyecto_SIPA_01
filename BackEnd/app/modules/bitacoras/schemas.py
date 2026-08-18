from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoBitacora


class BitacoraCreate(BaseModel):
    proceso_id: int
    numero_bitacora: int
    periodo_reportado: str = Field(..., pattern=r'^\d{4}-\d{2}$')
    titulo: str = Field(..., min_length=3, max_length=200)
    contenido: str = Field(..., min_length=10)
    archivo_f147_url: Optional[str] = Field(None, max_length=500)


class BitacoraUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    contenido: Optional[str] = Field(None, min_length=10)
    archivo_f147_url: Optional[str] = Field(None, max_length=500)


class BitacoraEvaluacion(BaseModel):
    estado: EstadoBitacora
    retroalimentacion: Optional[str] = Field(None, max_length=1000)


class BitacoraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proceso_id: int
    numero_bitacora: int
    periodo_reportado: str
    titulo: str
    contenido: str
    estado: EstadoBitacora
    fecha_envio: Optional[datetime]
    instructor_retroalimentacion: Optional[str]
    fecha_revision: Optional[datetime]
    archivo_f147_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BitacoraEvidenciaCreate(BaseModel):
    evidencia_archivo_id: int


class BitacoraEvidenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bitacora_id: int
    evidencia_archivo_id: int
    is_active: bool
    created_at: datetime