from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Empresa, CoordinadorEmpresa, ProcesoEtapaProductiva


# ================== Empresa ==================
def get_empresa(db: Session, empresa_id: int) -> Optional[Empresa]:
    return db.query(Empresa).filter(Empresa.id == empresa_id).first()


def get_empresa_by_nit(db: Session, nit: str) -> Optional[Empresa]:
    return db.query(Empresa).filter(Empresa.nit == nit).first()


def list_empresas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activas: bool = True,
    search: Optional[str] = None,
) -> list[Empresa]:
    query = db.query(Empresa)
    if solo_activas:
        query = query.filter(Empresa.is_active == True)
    if search:
        query = query.filter(
            or_(
                Empresa.razon_social.ilike(f"%{search}%"),
                Empresa.nit.ilike(f"%{search}%"),
            )
        )
    return query.offset(skip).limit(limit).all()


def create_empresa(db: Session, data: dict) -> Empresa:
    empresa = Empresa(**data)
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return empresa


def update_empresa(db: Session, empresa: Empresa, data: dict) -> Empresa:
    for key, value in data.items():
        setattr(empresa, key, value)
    db.commit()
    db.refresh(empresa)
    return empresa


def soft_delete_empresa(db: Session, empresa: Empresa) -> Empresa:
    empresa.is_active = False
    db.commit()
    db.refresh(empresa)
    return empresa


# ================== Coordinador de Empresa ==================
def get_coordinador_empresa(db: Session, coordinador_id: int) -> Optional[CoordinadorEmpresa]:
    return db.query(CoordinadorEmpresa).filter(
        CoordinadorEmpresa.id == coordinador_id
    ).first()


def get_coordinador_by_email(db: Session, email: str) -> Optional[CoordinadorEmpresa]:
    if not email:
        return None
    return db.query(CoordinadorEmpresa).filter(
        CoordinadorEmpresa.correo.ilike(email)
    ).first()


def list_coordinadores_empresa(
    db: Session,
    empresa_id: int,
    solo_activos: bool = True,
) -> list[CoordinadorEmpresa]:
    query = db.query(CoordinadorEmpresa).filter(
        CoordinadorEmpresa.empresa_id == empresa_id
    )
    if solo_activos:
        query = query.filter(CoordinadorEmpresa.is_active == True)
    return query.all()


def create_coordinador_empresa(db: Session, data: dict) -> CoordinadorEmpresa:
    coordinador = CoordinadorEmpresa(**data)
    db.add(coordinador)
    db.commit()
    db.refresh(coordinador)
    return coordinador


def update_coordinador_empresa(
    db: Session, coordinador: CoordinadorEmpresa, data: dict
) -> CoordinadorEmpresa:
    for key, value in data.items():
        setattr(coordinador, key, value)
    db.commit()
    db.refresh(coordinador)
    return coordinador


def soft_delete_coordinador_empresa(
    db: Session, coordinador: CoordinadorEmpresa
) -> CoordinadorEmpresa:
    coordinador.is_active = False
    db.commit()
    db.refresh(coordinador)
    return coordinador


# ================== Validaciones de dependencias ==================
def empresa_tiene_procesos_activos(db: Session, empresa_id: int) -> bool:
    """Retorna True si la empresa tiene procesos activos asociados."""
    count = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.empresa_id == empresa_id,
        ProcesoEtapaProductiva.is_active == True
    ).count()
    return count > 0


def coordinador_tiene_procesos_activos(db: Session, coordinador_id: int) -> bool:
    """Retorna True si el coordinador tiene procesos activos asociados."""
    count = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.coordinador_empresa_id == coordinador_id,
        ProcesoEtapaProductiva.is_active == True
    ).count()
    return count > 0