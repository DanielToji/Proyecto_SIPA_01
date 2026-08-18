from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tabla: str
    registro_id: int
    usuario_id: Optional[int]
    accion: str  # INSERT | UPDATE | DELETE
    datos_anteriores: Optional[dict]
    datos_nuevos: Optional[dict]
    created_at: datetime