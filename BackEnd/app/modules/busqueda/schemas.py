from typing import Optional, List
from pydantic import BaseModel


class ResultadoBusqueda(BaseModel):
    tipo: str  # usuario | instructor | programa | ficha | proceso
    id: int
    titulo: str
    subtitulo: Optional[str] = None
    descripcion: Optional[str] = None
    url: Optional[str] = None


class BusquedaResponse(BaseModel):
    total: int
    resultados: List[ResultadoBusqueda]