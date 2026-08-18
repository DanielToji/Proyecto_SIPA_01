from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import (
    Bitacora,
    BitacoraEvidencia,
    ProcesoEtapaProductiva,
    EstadoBitacora,
    EstadoProceso,
)


def get_bitacora(db: Session, bitacora_id: int) -> Optional[Bitacora]:
    return db.query(Bitacora).filter(Bitacora.id == bitacora_id).first()


def get_bitacora_by_proceso_numero(
    db: Session, proceso_id: int, numero_bitacora: int
) -> Optional[Bitacora]:
    """Valida que no exista otra bitácora con el mismo número para el proceso."""
    return db.query(Bitacora).filter(
        Bitacora.proceso_id == proceso_id,
        Bitacora.numero_bitacora == numero_bitacora,
        Bitacora.is_active == True,
    ).first()


def list_bitacoras(
    db: Session,
    proceso_id: Optional[int] = None,
    proceso_ids: Optional[List[int]] = None,
    ficha_id: Optional[int] = None,
    estado_bitacora: Optional[EstadoBitacora] = None,
    estado_proceso: Optional[EstadoProceso] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Bitacora]:
    query = db.query(Bitacora).join(
        ProcesoEtapaProductiva,
        Bitacora.proceso_id == ProcesoEtapaProductiva.id
    )
    if proceso_id:
        query = query.filter(Bitacora.proceso_id == proceso_id)
    if proceso_ids is not None:
        query = query.filter(Bitacora.proceso_id.in_(proceso_ids))
    if ficha_id:
        query = query.filter(ProcesoEtapaProductiva.ficha_id == ficha_id)
    if estado_bitacora:
        query = query.filter(Bitacora.estado == estado_bitacora)
    if estado_proceso:
        query = query.filter(ProcesoEtapaProductiva.estado == estado_proceso)
    if fecha_desde:
        query = query.filter(Bitacora.fecha_envio >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Bitacora.fecha_envio <= fecha_hasta)
    return query.order_by(Bitacora.fecha_envio.desc()).offset(skip).limit(limit).all()


def create_bitacora(db: Session, data: dict) -> Bitacora:
    bitacora = Bitacora(**data)
    db.add(bitacora)
    db.commit()
    db.refresh(bitacora)
    return bitacora


def update_bitacora(db: Session, bitacora: Bitacora, data: dict) -> Bitacora:
    for key, value in data.items():
        setattr(bitacora, key, value)
    db.commit()
    db.refresh(bitacora)
    return bitacora


def evaluar_bitacora(
    db: Session,
    bitacora: Bitacora,
    estado: EstadoBitacora,
    retroalimentacion: Optional[str] = None
) -> Bitacora:
    bitacora.estado = estado
    bitacora.instructor_retroalimentacion = retroalimentacion
    bitacora.fecha_revision = datetime.utcnow()
    db.commit()
    db.refresh(bitacora)
    return bitacora


def add_evidencia(db: Session, bitacora_id: int, evidencia_archivo_id: int) -> BitacoraEvidencia:
    nueva = BitacoraEvidencia(
        bitacora_id=bitacora_id,
        evidencia_archivo_id=evidencia_archivo_id,
        is_active=True
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def list_evidencias(db: Session, bitacora_id: int) -> list[BitacoraEvidencia]:
    return db.query(BitacoraEvidencia).filter(
        BitacoraEvidencia.bitacora_id == bitacora_id,
        BitacoraEvidencia.is_active == True
    ).all()