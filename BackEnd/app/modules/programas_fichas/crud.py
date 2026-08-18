from typing import Optional

from sqlalchemy.orm import Session

from app.models import (
    ProgramaFormacion,
    Ficha,
    AsignacionInstructorFicha,
    EstadoAsignacion,
)


# ================== Programa de Formación ==================
def get_programa(db: Session, programa_id: int) -> Optional[ProgramaFormacion]:
    return db.query(ProgramaFormacion).filter(ProgramaFormacion.id == programa_id).first()


def get_programa_by_codigo(db: Session, codigo: str) -> Optional[ProgramaFormacion]:
    return db.query(ProgramaFormacion).filter(ProgramaFormacion.codigo == codigo.strip()).first()


def list_programas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True,
    search: Optional[str] = None,
) -> list[ProgramaFormacion]:
    query = db.query(ProgramaFormacion)
    if solo_activos:
        query = query.filter(ProgramaFormacion.is_active == True)
    if search:
        query = query.filter(
            (ProgramaFormacion.nombre.ilike(f"%{search}%")) |
            (ProgramaFormacion.codigo.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()


def create_programa(db: Session, data: dict) -> ProgramaFormacion:
    programa = ProgramaFormacion(**data)
    db.add(programa)
    db.commit()
    db.refresh(programa)
    return programa


def update_programa(db: Session, programa: ProgramaFormacion, data: dict) -> ProgramaFormacion:
    for key, value in data.items():
        setattr(programa, key, value)
    db.commit()
    db.refresh(programa)
    return programa


def soft_delete_programa(db: Session, programa: ProgramaFormacion) -> ProgramaFormacion:
    programa.is_active = False
    db.commit()
    db.refresh(programa)
    return programa


# ================== Ficha ==================
def get_ficha(db: Session, ficha_id: int) -> Optional[Ficha]:
    return db.query(Ficha).filter(Ficha.id == ficha_id).first()


def get_ficha_by_numero(db: Session, numero_ficha: str) -> Optional[Ficha]:
    return db.query(Ficha).filter(Ficha.numero_ficha == numero_ficha.strip()).first()


def list_fichas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activas: bool = True,
    programa_id: Optional[int] = None,
    search: Optional[str] = None,
) -> list[Ficha]:
    query = db.query(Ficha)
    if solo_activas:
        query = query.filter(Ficha.is_active == True)
    if programa_id:
        query = query.filter(Ficha.programa_id == programa_id)
    if search:
        query = query.filter(Ficha.numero_ficha.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def create_ficha(db: Session, data: dict) -> Ficha:
    ficha = Ficha(**data)
    db.add(ficha)
    db.commit()
    db.refresh(ficha)
    return ficha


def update_ficha(db: Session, ficha: Ficha, data: dict) -> Ficha:
    for key, value in data.items():
        setattr(ficha, key, value)
    db.commit()
    db.refresh(ficha)
    return ficha


def soft_delete_ficha(db: Session, ficha: Ficha) -> Ficha:
    ficha.is_active = False
    db.commit()
    db.refresh(ficha)
    return ficha


# ================== Asignación Instructor-Ficha ==================
def get_asignacion_por_ficha_instructor(
    db: Session,
    ficha_id: int,
    instructor_id: int
) -> Optional[AsignacionInstructorFicha]:
    """Obtiene la asignación ficha-instructor sin importar su estado actual."""
    return db.query(AsignacionInstructorFicha).filter(
        AsignacionInstructorFicha.ficha_id == ficha_id,
        AsignacionInstructorFicha.instructor_id == instructor_id
    ).first()


def get_asignacion_activa(db: Session, ficha_id: int, instructor_id: int) -> Optional[AsignacionInstructorFicha]:
    return db.query(AsignacionInstructorFicha).filter(
        AsignacionInstructorFicha.ficha_id == ficha_id,
        AsignacionInstructorFicha.instructor_id == instructor_id,
        AsignacionInstructorFicha.estado_asignacion == EstadoAsignacion.ACTIVA,
        AsignacionInstructorFicha.is_active == True,
    ).first()


def list_asignaciones(
    db: Session,
    ficha_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    estado_asignacion: Optional[EstadoAsignacion] = None,
    solo_activas: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[AsignacionInstructorFicha]:
    query = db.query(AsignacionInstructorFicha)
    if ficha_id:
        query = query.filter(AsignacionInstructorFicha.ficha_id == ficha_id)
    if instructor_id:
        query = query.filter(AsignacionInstructorFicha.instructor_id == instructor_id)
    if estado_asignacion:
        query = query.filter(AsignacionInstructorFicha.estado_asignacion == estado_asignacion)
    if solo_activas:
        query = query.filter(AsignacionInstructorFicha.is_active == True)
    return query.offset(skip).limit(limit).all()

def create_asignacion(db: Session, data: dict) -> AsignacionInstructorFicha:
    asignacion = AsignacionInstructorFicha(**data)
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return asignacion


def update_asignacion(db: Session, asignacion: AsignacionInstructorFicha, data: dict) -> AsignacionInstructorFicha:
    for key, value in data.items():
        setattr(asignacion, key, value)
    db.commit()
    db.refresh(asignacion)
    return asignacion


def soft_delete_asignacion(db: Session, asignacion: AsignacionInstructorFicha) -> AsignacionInstructorFicha:
    asignacion.is_active = False
    db.commit()
    db.refresh(asignacion)
    return asignacion


def reactivar_asignacion(
    db: Session,
    asignacion: AsignacionInstructorFicha
) -> AsignacionInstructorFicha:
    """Reactiva una asignación previamente desactivada."""
    asignacion.is_active = True
    asignacion.estado_asignacion = EstadoAsignacion.ACTIVA
    db.commit()
    db.refresh(asignacion)
    return asignacion