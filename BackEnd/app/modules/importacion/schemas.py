from typing import List, Optional

from pydantic import BaseModel, Field


class RowError(BaseModel):
    """Detalle de error para una fila específica."""
    fila: int = Field(..., description="Número de fila en el archivo")
    mensaje: str = Field(..., description="Descripción del error")
    datos: Optional[dict] = Field(None, description="Datos de la fila con error")


class ImportResult(BaseModel):
    """Resultado de una operación de importación masiva."""
    total_filas: int = Field(..., description="Total de filas procesadas")
    filas_insertadas: int = Field(..., description="Filas insertadas correctamente")
    filas_con_error: int = Field(..., description="Filas con error")
    errores: List[RowError] = Field(default_factory=list, description="Lista detallada de errores")