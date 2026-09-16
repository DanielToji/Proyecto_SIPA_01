from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ============================================================
# ESQUEMAS DE BITÁCORAS
# ============================================================

class BitacoraBase(BaseModel):
    proceso_id: int
    numero_bitacora: int = Field(..., gt=0)
    periodo_reportado: str = Field(..., pattern=r'^\d{4}-\d{2}$')
    titulo: str = Field(..., max_length=200)
    contenido: str
    archivo_f147_url: Optional[str] = None


class BitacoraCreate(BitacoraBase):
    pass


class BitacoraUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=200)
    contenido: Optional[str] = None
    estado: Optional[str] = None
    instructor_retroalimentacion: Optional[str] = None


class BitacoraEvaluacion(BaseModel):
    estado: str
    retroalimentacion: Optional[str] = Field(None, max_length=1000)


class BitacoraOut(BitacoraBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    estado: str
    fecha_envio: Optional[datetime] = None
    fecha_revision: Optional[datetime] = None
    instructor_retroalimentacion: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class BitacoraListResponse(BaseModel):
    total: int
    items: list[BitacoraOut]


# ============================================================
# ESQUEMAS DE EVIDENCIAS
# ============================================================

class BitacoraEvidenciaBase(BaseModel):
    bitacora_id: int
    evidencia_archivo_id: int


class BitacoraEvidenciaCreate(BitacoraEvidenciaBase):
    pass


class BitacoraEvidenciaOut(BitacoraEvidenciaBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime