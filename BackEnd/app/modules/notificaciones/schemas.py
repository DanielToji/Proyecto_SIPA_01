from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoEnvioEmail


class NotificacionCreate(BaseModel):
    destinatario_usuario_id: int
    asunto: str = Field(..., min_length=3, max_length=200)
    cuerpo: str = Field(..., min_length=3)
    remitente_usuario_id: Optional[int] = None


class NotificacionUpdate(BaseModel):
    asunto: Optional[str] = Field(None, min_length=3, max_length=200)
    cuerpo: Optional[str] = Field(None, min_length=3)
    estado_envio_email: Optional[EstadoEnvioEmail] = None
    error_envio: Optional[str] = None
    is_active: Optional[bool] = None


class NotificacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remitente_usuario_id: Optional[int]
    destinatario_usuario_id: int
    asunto: str
    cuerpo: str
    fecha_creacion: datetime
    fecha_envio_email: Optional[datetime]
    estado_envio_email: EstadoEnvioEmail
    error_envio: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AlertaGenerada(BaseModel):
    destinatario_usuario_id: int
    asunto: str
    cuerpo: str


class AlertasResult(BaseModel):
    total_alertas_creadas: int
    alertas: list[NotificacionOut]


class EnvioCorreoResult(BaseModel):
    notificacion_id: int
    estado: EstadoEnvioEmail
    mensaje: str