from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models import (
    Usuario,
    Ficha,
    ProgramaFormacion,
    ProcesoEtapaProductiva,
    ReunionSeguimiento,
    ChecklistDocumentoProceso,
    Bitacora,
    EstadoProceso,
    EstadoDocumento,
    EstadoBitacora,
    EstadoSofia,
    TipoDocumento,
    ModalidadEP,
    Empresa,
)


def _nombre_completo(usuario: Optional[Usuario]) -> str:
    return f"{usuario.nombre} {usuario.apellido}" if usuario else ""


def get_datos_procesos_riesgo(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Procesos activos en riesgo, con clasificación."""
    hoy = date.today()
    query = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    procesos = query.all()
    rows = []
    for p in procesos:
        aprendiz = db.query(Usuario).filter(Usuario.id == p.aprendiz_id).first()
        ficha = db.query(Ficha).filter(Ficha.id == p.ficha_id).first()
        dias = (p.fecha_fin - hoy).days
        if dias < 0:
            riesgo = "VENCIDO"
        elif dias <= 15:
            riesgo = "VENCIDO"
        elif dias <= 30:
            riesgo = "CRITICO"
        elif dias <= 60:
            riesgo = "ATENCION"
        else:
            riesgo = "NORMAL"
        rows.append({
            "proceso_id": p.id,
            "aprendiz": _nombre_completo(aprendiz),
            "documento": aprendiz.documento_identidad if aprendiz else "",
            "ficha": ficha.numero_ficha if ficha else "",
            "fecha_inicio": p.fecha_inicio,
            "fecha_fin": p.fecha_fin,
            "dias_restantes": dias,
            "riesgo": riesgo,
            "instructor_id": p.instructor_id,
        })
    return rows


def get_datos_documentos_pendientes(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Documentos pendientes del checklist."""
    query = db.query(ChecklistDocumentoProceso).filter(
        ChecklistDocumentoProceso.estado == EstadoDocumento.PENDIENTE,
        ChecklistDocumentoProceso.is_active == True
    ).join(
        ProcesoEtapaProductiva,
        ChecklistDocumentoProceso.proceso_id == ProcesoEtapaProductiva.id
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    items = query.all()
    rows = []
    for item in items:
        proceso = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.id == item.proceso_id
        ).first()
        aprendiz = db.query(Usuario).filter(Usuario.id == proceso.aprendiz_id).first()
        ficha = db.query(Ficha).filter(Ficha.id == proceso.ficha_id).first()
        rows.append({
            "proceso_id": proceso.id,
            "aprendiz": _nombre_completo(aprendiz),
            "documento": aprendiz.documento_identidad if aprendiz else "",
            "ficha": ficha.numero_ficha if ficha else "",
            "tipo_documento": item.tipo_documento,
            "estado": item.estado.value,
        })
    return rows


def get_datos_seguimientos(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Seguimientos F023 con estado de realización."""
    query = db.query(ReunionSeguimiento).filter(
        ReunionSeguimiento.is_active == True
    ).join(
        ProcesoEtapaProductiva,
        ReunionSeguimiento.proceso_id == ProcesoEtapaProductiva.id
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    reuniones = query.all()
    rows = []
    for r in reuniones:
        proceso = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.id == r.proceso_id
        ).first()
        aprendiz = db.query(Usuario).filter(Usuario.id == proceso.aprendiz_id).first()
        ficha = db.query(Ficha).filter(Ficha.id == proceso.ficha_id).first()
        estado = "REALIZADO" if r.fecha_realizada else "PENDIENTE"
        rows.append({
            "proceso_id": proceso.id,
            "aprendiz": _nombre_completo(aprendiz),
            "ficha": ficha.numero_ficha if ficha else "",
            "momento": r.momento.value,
            "fecha_programada": r.fecha_programada.date(),
            "fecha_realizada": r.fecha_realizada.date() if r.fecha_realizada else "",
            "estado": estado,
        })
    return rows


def get_datos_bitacoras(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Bitácoras F147 con estado."""
    query = db.query(Bitacora).filter(Bitacora.is_active == True).join(
        ProcesoEtapaProductiva,
        Bitacora.proceso_id == ProcesoEtapaProductiva.id
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    bitacoras = query.all()
    rows = []
    for b in bitacoras:
        proceso = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.id == b.proceso_id
        ).first()
        aprendiz = db.query(Usuario).filter(Usuario.id == proceso.aprendiz_id).first()
        ficha = db.query(Ficha).filter(Ficha.id == proceso.ficha_id).first()
        rows.append({
            "bitacora_id": b.id,
            "proceso_id": proceso.id,
            "aprendiz": _nombre_completo(aprendiz),
            "ficha": ficha.numero_ficha if ficha else "",
            "numero_bitacora": b.numero_bitacora,
            "periodo": b.periodo_reportado,
            "titulo": b.titulo,
            "estado": b.estado.value,
            "fecha_envio": b.fecha_envio.date() if b.fecha_envio else "",
        })
    return rows


def get_datos_estado_aprendices(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Estado general de los aprendices en etapa productiva."""
    query = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.is_active == True
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    procesos = query.all()
    rows = []
    for p in procesos:
        aprendiz = db.query(Usuario).filter(Usuario.id == p.aprendiz_id).first()
        ficha = db.query(Ficha).filter(Ficha.id == p.ficha_id).first()
        programa = db.query(ProgramaFormacion).filter(
            ProgramaFormacion.id == ficha.programa_id if ficha else None
        ).first() if ficha else None
        modalidad = db.query(ModalidadEP).filter(ModalidadEP.id == p.modalidad_id).first()
        empresa = db.query(Empresa).filter(Empresa.id == p.empresa_id).first() if p.empresa_id else None
        rows.append({
            "proceso_id": p.id,
            "aprendiz": _nombre_completo(aprendiz),
            "documento": aprendiz.documento_identidad if aprendiz else "",
            "ficha": ficha.numero_ficha if ficha else "",
            "programa": programa.nombre if programa else "",
            "modalidad": modalidad.nombre if modalidad else "",
            "empresa": empresa.razon_social if empresa else "",
            "fecha_inicio": p.fecha_inicio,
            "fecha_fin": p.fecha_fin,
            "estado": p.estado.value,
            "estado_sofia": p.estado_sofia.value,
        })
    return rows


def get_datos_alternativas(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Alternativas de etapa productiva seleccionadas por aprendices."""
    return get_datos_estado_aprendices(db, instructor_id)


def get_datos_aprendices_sin_alternativa(db: Session) -> List[Dict[str, Any]]:
    """Aprendices activos sin proceso de etapa productiva."""
    subquery = db.query(ProcesoEtapaProductiva.aprendiz_id).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).subquery()

    aprendices = db.query(Usuario).filter(
        Usuario.rol_id == 4,
        Usuario.is_active == True,
        Usuario.id.notin_(subquery)
    ).all()

    rows = []
    for a in aprendices:
        rows.append({
            "aprendiz_id": a.id,
            "aprendiz": _nombre_completo(a),
            "documento": a.documento_identidad or "",
            "email": a.email,
            "telefono": a.telefono or "",
        })
    return rows


def get_datos_evaluados_sin_evaluar(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Procesos evaluados y sin evaluar (notas y SOFIA)."""
    query = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.is_active == True
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    procesos = query.all()
    rows = []
    for p in procesos:
        aprendiz = db.query(Usuario).filter(Usuario.id == p.aprendiz_id).first()
        ficha = db.query(Ficha).filter(Ficha.id == p.ficha_id).first()
        evaluado = p.nota_empresa is not None and p.nota_instructor is not None
        rows.append({
            "proceso_id": p.id,
            "aprendiz": _nombre_completo(aprendiz),
            "ficha": ficha.numero_ficha if ficha else "",
            "nota_empresa": p.nota_empresa if p.nota_empresa is not None else "",
            "nota_instructor": p.nota_instructor if p.nota_instructor is not None else "",
            "estado_sofia": p.estado_sofia.value,
            "evaluado": "SI" if evaluado else "NO",
        })
    return rows


def get_datos_indicadores_gestion(db: Session) -> List[Dict[str, Any]]:
    """Indicadores globales de gestión."""
    total_aprendices = db.query(func.count(Usuario.id)).filter(
        Usuario.rol_id == 4, Usuario.is_active == True
    ).scalar() or 0
    total_procesos_activos = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    total_procesos_finalizados = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.FINALIZADO,
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    total_en_riesgo = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.fecha_fin <= date.today() + timedelta(days=30),
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    docs_pendientes = db.query(func.count(ChecklistDocumentoProceso.id)).filter(
        ChecklistDocumentoProceso.estado == EstadoDocumento.PENDIENTE,
        ChecklistDocumentoProceso.is_active == True
    ).scalar() or 0

    return [{
        "indicador": "Total aprendices activos",
        "valor": total_aprendices,
    }, {
        "indicador": "Procesos activos",
        "valor": total_procesos_activos,
    }, {
        "indicador": "Procesos finalizados",
        "valor": total_procesos_finalizados,
    }, {
        "indicador": "Procesos en riesgo (<=30 días)",
        "valor": total_en_riesgo,
    }, {
        "indicador": "Documentos pendientes",
        "valor": docs_pendientes,
    }]