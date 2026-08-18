from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Auditoria


def list_auditoria(
    db: Session,
    tabla: Optional[str] = None,
    usuario_id: Optional[int] = None,
    accion: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Auditoria]:
    """
    Consulta el historial de auditoría con filtros opcionales.
    Retorna los registros ordenados de más reciente a más antiguo.
    """
    query = db.query(Auditoria)

    if tabla:
        query = query.filter(Auditoria.tabla == tabla)
    if usuario_id:
        query = query.filter(Auditoria.usuario_id == usuario_id)
    if accion:
        query = query.filter(Auditoria.accion == accion)
    if desde:
        query = query.filter(Auditoria.created_at >= desde)
    if hasta:
        query = query.filter(Auditoria.created_at <= hasta)

    return query.order_by(Auditoria.created_at.desc()).offset(skip).limit(limit).all()


def count_auditoria(
    db: Session,
    tabla: Optional[str] = None,
    usuario_id: Optional[int] = None,
    accion: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
) -> int:
    """
    Retorna el total de registros de auditoría que coinciden con los filtros.
    Útil para paginación en el frontend.
    """
    query = db.query(Auditoria)

    if tabla:
        query = query.filter(Auditoria.tabla == tabla)
    if usuario_id:
        query = query.filter(Auditoria.usuario_id == usuario_id)
    if accion:
        query = query.filter(Auditoria.accion == accion)
    if desde:
        query = query.filter(Auditoria.created_at >= desde)
    if hasta:
        query = query.filter(Auditoria.created_at <= hasta)

    return query.count()