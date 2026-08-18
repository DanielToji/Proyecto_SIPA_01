from datetime import date, timedelta, datetime
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import (
    NotificacionMensaje,
    ProcesoEtapaProductiva,
    Usuario,
    ReunionSeguimiento,
    ChecklistDocumentoProceso,
    EstadoEnvioEmail,
    EstadoProceso,
    EstadoDocumento,
    MomentoReunion,
)

# Umbrales de alerta (según requerimiento ajustado)
DIAS_PARA_PROXIMA_FINALIZACION = 15


def get_notificacion(db: Session, notificacion_id: int) -> Optional[NotificacionMensaje]:
    return db.query(NotificacionMensaje).filter(
        NotificacionMensaje.id == notificacion_id
    ).first()


def list_notificaciones_usuario(
    db: Session,
    usuario_id: int,
    solo_activas: bool = True,
    estado_envio: Optional[EstadoEnvioEmail] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[NotificacionMensaje]:
    query = db.query(NotificacionMensaje).filter(
        NotificacionMensaje.destinatario_usuario_id == usuario_id
    )
    if solo_activas:
        query = query.filter(NotificacionMensaje.is_active == True)
    if estado_envio:
        query = query.filter(NotificacionMensaje.estado_envio_email == estado_envio)
    return query.order_by(NotificacionMensaje.fecha_creacion.desc()).offset(skip).limit(limit).all()


def create_notificacion(db: Session, data: dict) -> NotificacionMensaje:
    notificacion = NotificacionMensaje(**data)
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def update_notificacion(
    db: Session, notificacion: NotificacionMensaje, data: dict
) -> NotificacionMensaje:
    for key, value in data.items():
        setattr(notificacion, key, value)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def soft_delete_notificacion(
    db: Session, notificacion: NotificacionMensaje
) -> NotificacionMensaje:
    notificacion.is_active = False
    db.commit()
    db.refresh(notificacion)
    return notificacion


def marcar_notificacion_enviada(
    db: Session, notificacion: NotificacionMensaje
) -> NotificacionMensaje:
    notificacion.estado_envio_email = EstadoEnvioEmail.ENVIADO
    notificacion.fecha_envio_email = datetime.utcnow()
    db.commit()
    db.refresh(notificacion)
    return notificacion


# ============================================================
# Utilidades para alertas automáticas
# ============================================================
def _existe_notificacion_similar(
    db: Session, destinatario_id: int, asunto: str
) -> bool:
    """Evita duplicados exactos en el mismo día."""
    hoy = date.today()
    count = db.query(NotificacionMensaje).filter(
        NotificacionMensaje.destinatario_usuario_id == destinatario_id,
        NotificacionMensaje.asunto == asunto,
        func.date(NotificacionMensaje.fecha_creacion) == hoy,
        NotificacionMensaje.is_active == True
    ).count()
    return count > 0


def _crear_notificacion_si_no_existe(
    db: Session,
    destinatario_id: int,
    asunto: str,
    cuerpo: str,
    remitente_usuario_id: Optional[int] = None,
) -> Optional[NotificacionMensaje]:
    """Crea una notificación si no existe otra similar hoy para el destinatario."""
    if _existe_notificacion_similar(db, destinatario_id, asunto):
        return None
    notificacion = NotificacionMensaje(
        destinatario_usuario_id=destinatario_id,
        remitente_usuario_id=remitente_usuario_id,
        asunto=asunto,
        cuerpo=cuerpo,
        estado_envio_email=EstadoEnvioEmail.PENDIENTE,
        is_active=True,
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion