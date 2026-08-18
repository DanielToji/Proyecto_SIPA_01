from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models import ReunionSeguimiento, MomentoReunion


def get_reunion(db: Session, reunion_id: int) -> Optional[ReunionSeguimiento]:
    return db.query(ReunionSeguimiento).filter(ReunionSeguimiento.id == reunion_id).first()


def get_reunion_by_proceso_momento(
    db: Session, proceso_id: int, momento: MomentoReunion
) -> Optional[ReunionSeguimiento]:
    return db.query(ReunionSeguimiento).filter(
        ReunionSeguimiento.proceso_id == proceso_id,
        ReunionSeguimiento.momento == momento,
    ).first()


def list_reuniones(
    db: Session,
    proceso_id: Optional[int] = None,
    proceso_ids: Optional[List[int]] = None,
    instructor_id: Optional[int] = None,
    momento: Optional[MomentoReunion] = None,
    solo_activas: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[ReunionSeguimiento]:
    query = db.query(ReunionSeguimiento)
    if solo_activas:
        query = query.filter(ReunionSeguimiento.is_active == True)
    if proceso_id:
        query = query.filter(ReunionSeguimiento.proceso_id == proceso_id)
    if proceso_ids is not None:
        query = query.filter(ReunionSeguimiento.proceso_id.in_(proceso_ids))
    if instructor_id:
        query = query.filter(ReunionSeguimiento.instructor_id == instructor_id)
    if momento:
        query = query.filter(ReunionSeguimiento.momento == momento)
    return query.offset(skip).limit(limit).all()


def list_reuniones_vencidas(
    db: Session,
    instructor_id: Optional[int] = None,
    proceso_ids: Optional[List[int]] = None,
) -> list[ReunionSeguimiento]:
    """
    Retorna reuniones con fecha_programada anterior a hoy, no realizadas y activas.
    RF-09: Momentos vencidos.
    """
    hoy = datetime.utcnow()
    query = db.query(ReunionSeguimiento).filter(
        ReunionSeguimiento.fecha_programada < hoy,
        ReunionSeguimiento.fecha_realizada.is_(None),
        ReunionSeguimiento.is_active == True
    )
    if instructor_id:
        query = query.filter(ReunionSeguimiento.instructor_id == instructor_id)
    if proceso_ids is not None:
        query = query.filter(ReunionSeguimiento.proceso_id.in_(proceso_ids))
    return query.all()


def create_reunion(db: Session, data: dict) -> ReunionSeguimiento:
    reunion = ReunionSeguimiento(**data)
    db.add(reunion)
    db.commit()
    db.refresh(reunion)
    return reunion


def update_reunion(db: Session, reunion: ReunionSeguimiento, data: dict) -> ReunionSeguimiento:
    for key, value in data.items():
        setattr(reunion, key, value)
    db.commit()
    db.refresh(reunion)
    return reunion


def soft_delete_reunion(db: Session, reunion: ReunionSeguimiento) -> ReunionSeguimiento:
    reunion.is_active = False
    db.commit()
    db.refresh(reunion)
    return reunion