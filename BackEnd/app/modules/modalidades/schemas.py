from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ModalidadEPBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre de la modalidad")
    descripcion: Optional[str] = Field(None, max_length=500)


class ModalidadEPCreate(ModalidadEPBase):
    pass


class ModalidadEPUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ModalidadEPOut(ModalidadEPBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime