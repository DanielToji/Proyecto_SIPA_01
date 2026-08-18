from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoProceso, EstadoSofia, EstadoDocumento, TipoNovedad


# ================== Proceso Etapa Productiva ==================
class ProcesoBase(BaseModel):
    aprendiz_id: int
    ficha_id: int
    modalidad_id: int
    empresa_id: Optional[int] = None
    coordinador_empresa_id: Optional[int] = None
    instructor_id: int
    fecha_inicio: date
    fecha_fin: date
    observaciones: Optional[str] = Field(None, max_length=1000)


class ProcesoCreate(ProcesoBase):
    pass


class ProcesoUpdate(BaseModel):
    empresa_id: Optional[int] = None
    coordinador_empresa_id: Optional[int] = None
    instructor_id: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[EstadoProceso] = None
    estado_sofia: Optional[EstadoSofia] = None
    nota_empresa: Optional[float] = Field(None, ge=0, le=10)
    nota_instructor: Optional[float] = Field(None, ge=0, le=10)
    observaciones: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class ProcesoOut(ProcesoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoProceso
    estado_sofia: EstadoSofia
    nota_empresa: Optional[float]
    nota_instructor: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ================== Checklist Documental ==================
class ChecklistDocumentoBase(BaseModel):
    tipo_documento: str = Field(..., min_length=2, max_length=50)
    estado: EstadoDocumento = EstadoDocumento.PENDIENTE
    evidencia_archivo_id: Optional[int] = None


class ChecklistDocumentoCreate(ChecklistDocumentoBase):
    pass


class ChecklistDocumentoUpdate(BaseModel):
    tipo_documento: Optional[str] = Field(None, min_length=2, max_length=50)
    estado: Optional[EstadoDocumento] = None
    evidencia_archivo_id: Optional[int] = None
    is_active: Optional[bool] = None


class ChecklistDocumentoOut(ChecklistDocumentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proceso_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ================== Evaluación Final ==================
class EvaluacionFinalUpdate(BaseModel):
    """Actualización de evaluación final del proceso."""
    nota_empresa: Optional[float] = Field(None, ge=0, le=10, description="Nota asignada por la empresa (0-10)")
    nota_instructor: Optional[float] = Field(None, ge=0, le=10, description="Nota asignada por el instructor (0-10)")
    estado_sofia: Optional[EstadoSofia] = None
    estado: Optional[EstadoProceso] = None
    observaciones: Optional[str] = Field(None, max_length=1000)


class EvaluacionFinalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoProceso
    estado_sofia: EstadoSofia
    nota_empresa: Optional[float]
    nota_instructor: Optional[float]
    observaciones: Optional[str]
    updated_at: datetime


    # ================== Novedades de Proceso ==================
class NovedadProcesoBase(BaseModel):
    tipo_novedad: TipoNovedad
    fecha_novedad: date
    descripcion: str = Field(..., min_length=5, max_length=2000)
    documento_soporte_url: Optional[str] = Field(None, max_length=500)


class NovedadProcesoCreate(NovedadProcesoBase):
    pass


class NovedadProcesoUpdate(BaseModel):
    tipo_novedad: Optional[TipoNovedad] = None
    fecha_novedad: Optional[date] = None
    descripcion: Optional[str] = Field(None, min_length=5, max_length=2000)
    documento_soporte_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class NovedadProcesoOut(NovedadProcesoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proceso_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime  


    # ================== Avance del Proceso ==================
class ProcesoAvance(BaseModel):
    proceso_id: int
    avance: float
    momentos_completados: int
    total_momentos: int = 3