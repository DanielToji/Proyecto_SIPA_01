from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class ReporteFiltros(BaseModel):
    """Filtros opcionales para reportes."""
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    programa_id: Optional[int] = None
    ficha_id: Optional[int] = None
    instructor_id: Optional[int] = None


class ReporteResponse(BaseModel):
    """Respuesta informativa cuando no se descarga archivo."""
    mensaje: str
    total_registros: int
    formato: str