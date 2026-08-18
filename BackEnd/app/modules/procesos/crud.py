from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models import (
    ProcesoEtapaProductiva,
    ChecklistDocumentoProceso,
    ReunionSeguimiento,
    EstadoProceso,
    EstadoSofia,
    NovedadProceso,
    TipoNovedad,
)


# ================== Proceso ==================
def get_proceso(db: Session, proceso_id: int) -> Optional[ProcesoEtapaProductiva]:
    return db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == proceso_id
    ).first()


def list_procesos(
    db: Session,
    aprendiz_id: Optional[int] = None,
    ficha_id: Optional[int] = None,
    modalidad_id: Optional[int] = None,
    empresa_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    estado: Optional[EstadoProceso] = None,
    estado_sofia: Optional[EstadoSofia] = None,
    fecha_inicio_desde: Optional[date] = None,
    fecha_inicio_hasta: Optional[date] = None,
    fecha_fin_desde: Optional[date] = None,
    fecha_fin_hasta: Optional[date] = None,
    solo_activos: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[ProcesoEtapaProductiva]:
    query = db.query(ProcesoEtapaProductiva)
    if solo_activos:
        query = query.filter(ProcesoEtapaProductiva.is_active == True)
    if aprendiz_id:
        query = query.filter(ProcesoEtapaProductiva.aprendiz_id == aprendiz_id)
    if ficha_id:
        query = query.filter(ProcesoEtapaProductiva.ficha_id == ficha_id)
    if modalidad_id:
        query = query.filter(ProcesoEtapaProductiva.modalidad_id == modalidad_id)
    if empresa_id:
        query = query.filter(ProcesoEtapaProductiva.empresa_id == empresa_id)
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)
    if estado:
        query = query.filter(ProcesoEtapaProductiva.estado == estado)
    if estado_sofia:
        query = query.filter(ProcesoEtapaProductiva.estado_sofia == estado_sofia)
    if fecha_inicio_desde:
        query = query.filter(ProcesoEtapaProductiva.fecha_inicio >= fecha_inicio_desde)
    if fecha_inicio_hasta:
        query = query.filter(ProcesoEtapaProductiva.fecha_inicio <= fecha_inicio_hasta)
    if fecha_fin_desde:
        query = query.filter(ProcesoEtapaProductiva.fecha_fin >= fecha_fin_desde)
    if fecha_fin_hasta:
        query = query.filter(ProcesoEtapaProductiva.fecha_fin <= fecha_fin_hasta)
    return query.offset(skip).limit(limit).all()


def create_proceso(db: Session, data: dict) -> ProcesoEtapaProductiva:
    proceso = ProcesoEtapaProductiva(**data)
    db.add(proceso)
    db.commit()
    db.refresh(proceso)
    return proceso


def update_proceso(db: Session, proceso: ProcesoEtapaProductiva, data: dict) -> ProcesoEtapaProductiva:
    for key, value in data.items():
        setattr(proceso, key, value)
    db.commit()
    db.refresh(proceso)
    return proceso


def soft_delete_proceso(db: Session, proceso: ProcesoEtapaProductiva) -> ProcesoEtapaProductiva:
    proceso.is_active = False
    db.commit()
    db.refresh(proceso)
    return proceso


# ================== Checklist Documental ==================
def get_checklist_item(db: Session, item_id: int) -> Optional[ChecklistDocumentoProceso]:
    return db.query(ChecklistDocumentoProceso).filter(
        ChecklistDocumentoProceso.id == item_id
    ).first()


def get_checklist_item_by_tipo(
    db: Session, proceso_id: int, tipo_documento: str
) -> Optional[ChecklistDocumentoProceso]:
    return db.query(ChecklistDocumentoProceso).filter(
        ChecklistDocumentoProceso.proceso_id == proceso_id,
        ChecklistDocumentoProceso.tipo_documento == tipo_documento,
    ).first()


def list_checklist_proceso(
    db: Session,
    proceso_id: int,
    solo_activos: bool = True,
) -> list[ChecklistDocumentoProceso]:
    query = db.query(ChecklistDocumentoProceso).filter(
        ChecklistDocumentoProceso.proceso_id == proceso_id
    )
    if solo_activos:
        query = query.filter(ChecklistDocumentoProceso.is_active == True)
    return query.all()


def create_checklist_item(db: Session, data: dict) -> ChecklistDocumentoProceso:
    item = ChecklistDocumentoProceso(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_checklist_item(
    db: Session, item: ChecklistDocumentoProceso, data: dict
) -> ChecklistDocumentoProceso:
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def soft_delete_checklist_item(
    db: Session, item: ChecklistDocumentoProceso
) -> ChecklistDocumentoProceso:
    item.is_active = False
    db.commit()
    db.refresh(item)
    return item


# ================== Novedades de Proceso ==================
def get_novedad(db: Session, novedad_id: int) -> Optional[NovedadProceso]:
    return db.query(NovedadProceso).filter(NovedadProceso.id == novedad_id).first()


def list_novedades(
    db: Session,
    proceso_id: Optional[int] = None,
    tipo_novedad: Optional[TipoNovedad] = None,
    solo_activas: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> list[NovedadProceso]:
    query = db.query(NovedadProceso)
    if solo_activas:
        query = query.filter(NovedadProceso.is_active == True)
    if proceso_id:
        query = query.filter(NovedadProceso.proceso_id == proceso_id)
    if tipo_novedad:
        query = query.filter(NovedadProceso.tipo_novedad == tipo_novedad)
    return query.offset(skip).limit(limit).all()


def create_novedad(db: Session, data: dict) -> NovedadProceso:
    novedad = NovedadProceso(**data)
    db.add(novedad)
    db.commit()
    db.refresh(novedad)
    return novedad


def update_novedad(db: Session, novedad: NovedadProceso, data: dict) -> NovedadProceso:
    for key, value in data.items():
        setattr(novedad, key, value)
    db.commit()
    db.refresh(novedad)
    return novedad


def soft_delete_novedad(db: Session, novedad: NovedadProceso) -> NovedadProceso:
    novedad.is_active = False
    db.commit()
    db.refresh(novedad)
    return novedad


def calcular_avance_proceso(db: Session, proceso_id: int) -> dict:
    """
    Calcula el porcentaje de avance del proceso según los momentos de seguimiento completados.
    RF-07: Porcentaje de avance y gráfica de avance.
    """
    momentos = ["MOMENTO_1_INICIAL", "MOMENTO_2_PARCIAL", "MOMENTO_3_FINAL"]
    completados = db.query(ReunionSeguimiento).filter(
        ReunionSeguimiento.proceso_id == proceso_id,
        ReunionSeguimiento.momento.in_(momentos),
        ReunionSeguimiento.fecha_realizada.isnot(None),
        ReunionSeguimiento.is_active == True
    ).count()
    avance = round((completados / 3) * 100, 2)
    return {
        "proceso_id": proceso_id,
        "avance": avance,
        "momentos_completados": completados,
        "total_momentos": 3,
    }