from typing import Optional

from sqlalchemy.orm import Session

from app.models import ModalidadEP
from app.models import ModalidadEP, ProcesoEtapaProductiva


def get_modalidad(db: Session, modalidad_id: int) -> Optional[ModalidadEP]:
    """Obtiene una modalidad por su ID."""
    return db.query(ModalidadEP).filter(ModalidadEP.id == modalidad_id).first()


def get_modalidad_by_nombre(db: Session, nombre: str) -> Optional[ModalidadEP]:
    """Busca una modalidad por nombre exacto (sin distinguir mayúsculas)."""
    return db.query(ModalidadEP).filter(
        ModalidadEP.nombre.ilike(nombre.strip())
    ).first()


def list_modalidades(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activas: bool = True,
    search: Optional[str] = None,
) -> list[ModalidadEP]:
    """Lista modalidades con filtros opcionales."""
    query = db.query(ModalidadEP)
    if solo_activas:
        query = query.filter(ModalidadEP.is_active == True)
    if search:
        query = query.filter(ModalidadEP.nombre.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def create_modalidad(db: Session, data: dict) -> ModalidadEP:
    """Crea una nueva modalidad."""
    modalidad = ModalidadEP(**data)
    db.add(modalidad)
    db.commit()
    db.refresh(modalidad)
    return modalidad


def update_modalidad(db: Session, modalidad: ModalidadEP, data: dict) -> ModalidadEP:
    """Actualiza campos de una modalidad existente."""
    for key, value in data.items():
        setattr(modalidad, key, value)
    db.commit()
    db.refresh(modalidad)
    return modalidad


def soft_delete_modalidad(db: Session, modalidad: ModalidadEP) -> ModalidadEP:
    """Desactiva una modalidad (soft delete)."""
    modalidad.is_active = False
    db.commit()
    db.refresh(modalidad)
    return modalidad

def modalidad_tiene_procesos_activos(db: Session, modalidad_id: int) -> bool:
    """Retorna True si la modalidad tiene procesos activos asociados."""
    count = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.modalidad_id == modalidad_id,
        ProcesoEtapaProductiva.is_active == True
    ).count()
    return count > 0