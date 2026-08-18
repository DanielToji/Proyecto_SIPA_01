from typing import Optional

from sqlalchemy.orm import Session

from app.models import Charla, AsistenciaCharla


# ================== Charla ==================
def get_charla(db: Session, charla_id: int) -> Optional[Charla]:
    return db.query(Charla).filter(Charla.id == charla_id).first()


def list_charlas(
    db: Session,
    ficha_id: Optional[int] = None,
    tipo_charla: Optional[str] = None,
    instructor_id: Optional[int] = None,
    solo_activas: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[Charla]:
    query = db.query(Charla)
    if solo_activas:
        query = query.filter(Charla.is_active == True)
    if ficha_id:
        query = query.filter(Charla.ficha_id == ficha_id)
    if tipo_charla:
        query = query.filter(Charla.tipo_charla == tipo_charla)
    if instructor_id:
        query = query.filter(Charla.instructor_id == instructor_id)
    return query.offset(skip).limit(limit).all()


def create_charla(db: Session, data: dict) -> Charla:
    charla = Charla(**data)
    db.add(charla)
    db.commit()
    db.refresh(charla)
    return charla


def update_charla(db: Session, charla: Charla, data: dict) -> Charla:
    for key, value in data.items():
        setattr(charla, key, value)
    db.commit()
    db.refresh(charla)
    return charla


def soft_delete_charla(db: Session, charla: Charla) -> Charla:
    charla.is_active = False
    db.commit()
    db.refresh(charla)
    return charla


# ================== Asistencia ==================
def get_asistencia(db: Session, asistencia_id: int) -> Optional[AsistenciaCharla]:
    return db.query(AsistenciaCharla).filter(AsistenciaCharla.id == asistencia_id).first()


def get_asistencia_by_charla_aprendiz(
    db: Session, charla_id: int, aprendiz_id: int
) -> Optional[AsistenciaCharla]:
    return db.query(AsistenciaCharla).filter(
        AsistenciaCharla.charla_id == charla_id,
        AsistenciaCharla.aprendiz_id == aprendiz_id,
    ).first()


def list_asistencias_charla(
    db: Session,
    charla_id: int,
    aprendiz_id: Optional[int] = None,
    solo_activas: bool = True,
) -> list[AsistenciaCharla]:
    query = db.query(AsistenciaCharla).filter(AsistenciaCharla.charla_id == charla_id)
    if aprendiz_id:
        query = query.filter(AsistenciaCharla.aprendiz_id == aprendiz_id)
    if solo_activas:
        query = query.filter(AsistenciaCharla.is_active == True)
    return query.all()


def create_asistencia(db: Session, data: dict) -> AsistenciaCharla:
    asistencia = AsistenciaCharla(**data)
    db.add(asistencia)
    db.commit()
    db.refresh(asistencia)
    return asistencia


def update_asistencia(db: Session, asistencia: AsistenciaCharla, data: dict) -> AsistenciaCharla:
    for key, value in data.items():
        setattr(asistencia, key, value)
    db.commit()
    db.refresh(asistencia)
    return asistencia


def soft_delete_asistencia(db: Session, asistencia: AsistenciaCharla) -> AsistenciaCharla:
    asistencia.is_active = False
    db.commit()
    db.refresh(asistencia)
    return asistencia