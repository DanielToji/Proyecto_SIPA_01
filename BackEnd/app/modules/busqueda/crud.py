from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import (
    Usuario,
    Ficha,
    ProgramaFormacion,
    ProcesoEtapaProductiva,
    AsignacionInstructorFicha,
)


def _limpiar_texto(q: str) -> str:
    """Elimina comodines SQL para evitar uso malintencionado."""
    return q.replace("%", "").replace("_", "").strip()


def buscar_usuarios(
    db: Session,
    q: str,
    rol_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    limit: int = 20,
) -> List[Usuario]:
    """Busca usuarios por nombre, apellido, email o documento."""
    q = _limpiar_texto(q)
    query = db.query(Usuario)
    if rol_id:
        query = query.filter(Usuario.rol_id == rol_id)

    # Si el usuario es instructor, restringir a aprendices de sus procesos
    if instructor_id is not None:
        subquery = db.query(ProcesoEtapaProductiva.aprendiz_id).filter(
            ProcesoEtapaProductiva.instructor_id == instructor_id,
            ProcesoEtapaProductiva.is_active == True
        ).subquery()
        query = query.filter(Usuario.id.in_(subquery))

    query = query.filter(
        or_(
            Usuario.nombre.ilike(f"%{q}%"),
            Usuario.apellido.ilike(f"%{q}%"),
            Usuario.email.ilike(f"%{q}%"),
            Usuario.documento_identidad.ilike(f"%{q}%"),
        )
    )
    return query.limit(limit).all()


def buscar_instructores(
    db: Session,
    q: str,
    limit: int = 20,
) -> List[Usuario]:
    """Busca instructores por nombre, apellido, email o documento."""
    q = _limpiar_texto(q)
    return db.query(Usuario).filter(
        Usuario.rol_id == 3,
        Usuario.is_active == True,
        or_(
            Usuario.nombre.ilike(f"%{q}%"),
            Usuario.apellido.ilike(f"%{q}%"),
            Usuario.email.ilike(f"%{q}%"),
            Usuario.documento_identidad.ilike(f"%{q}%"),
        )
    ).limit(limit).all()


def buscar_programas(
    db: Session,
    q: str,
    limit: int = 20,
) -> List[ProgramaFormacion]:
    """Busca programas de formación por código o nombre."""
    q = _limpiar_texto(q)
    return db.query(ProgramaFormacion).filter(
        ProgramaFormacion.is_active == True,
        or_(
            ProgramaFormacion.codigo.ilike(f"%{q}%"),
            ProgramaFormacion.nombre.ilike(f"%{q}%"),
        )
    ).limit(limit).all()


def buscar_fichas(
    db: Session,
    q: str,
    instructor_id: Optional[int] = None,
    limit: int = 20,
) -> List[Ficha]:
    """Busca fichas por número. Si es instructor, restringe a sus asignaciones."""
    q = _limpiar_texto(q)
    query = db.query(Ficha).filter(Ficha.is_active == True)

    if instructor_id is not None:
        query = query.join(
            AsignacionInstructorFicha,
            AsignacionInstructorFicha.ficha_id == Ficha.id
        ).filter(AsignacionInstructorFicha.instructor_id == instructor_id)

    query = query.filter(Ficha.numero_ficha.ilike(f"%{q}%"))
    return query.limit(limit).all()


def buscar_procesos(
    db: Session,
    q: str,
    instructor_id: Optional[int] = None,
    aprendiz_id: Optional[int] = None,
    limit: int = 20,
) -> List[ProcesoEtapaProductiva]:
    """
    Busca procesos por:
    - nombre/apellido/documento del aprendiz
    - número de ficha
    """
    q = _limpiar_texto(q)
    query = db.query(ProcesoEtapaProductiva).join(
        Usuario, ProcesoEtapaProductiva.aprendiz_id == Usuario.id
    ).join(
        Ficha, ProcesoEtapaProductiva.ficha_id == Ficha.id
    )

    if instructor_id is not None:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)
    if aprendiz_id is not None:
        query = query.filter(ProcesoEtapaProductiva.aprendiz_id == aprendiz_id)

    query = query.filter(
        or_(
            Usuario.nombre.ilike(f"%{q}%"),
            Usuario.apellido.ilike(f"%{q}%"),
            Usuario.documento_identidad.ilike(f"%{q}%"),
            Ficha.numero_ficha.ilike(f"%{q}%"),
        )
    )
    return query.limit(limit).all()