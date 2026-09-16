from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models import (
    Usuario,
    Ficha,
    ProgramaFormacion,
    AsignacionInstructorFicha,
    ProcesoEtapaProductiva,
    Bitacora,
    ReunionSeguimiento,
    ChecklistDocumentoProceso,
    MedidasFormativasProceso,
    NovedadProceso,
    EstadoBitacora,
    EstadoProceso,
    EstadoDocumento,
    EstadoMedidaFormativa,
    MomentoReunion,
)


def _clasificar_riesgo(fecha_fin: date) -> str:
    hoy = date.today()
    dias = (fecha_fin - hoy).days
    if dias < 0:
        return "VENCIDO"
    elif dias <= 15:
        return "VENCIDO"
    elif dias <= 30:
        return "CRITICO"
    elif dias <= 60:
        return "ATENCION"
    return "NORMAL"


def _obtener_procesos_riesgo(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    query = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    procesos = query.all()
    resultado = []
    for p in procesos:
        aprendiz = db.query(Usuario).filter(Usuario.id == p.aprendiz_id).first()
        ficha = db.query(Ficha).filter(Ficha.id == p.ficha_id).first()
        dias = (p.fecha_fin - date.today()).days
        resultado.append({
            "proceso_id": p.id,
            "aprendiz_id": p.aprendiz_id,
            "nombre_aprendiz": f"{aprendiz.nombre} {aprendiz.apellido}" if aprendiz else None,
            "ficha_id": p.ficha_id,
            "numero_ficha": ficha.numero_ficha if ficha else None,
            "fecha_fin": p.fecha_fin,
            "dias_restantes": dias,
            "estado_riesgo": _clasificar_riesgo(p.fecha_fin),
        })

    orden = {"VENCIDO": 0, "CRITICO": 1, "ATENCION": 2, "NORMAL": 3}
    resultado.sort(key=lambda x: (orden.get(x["estado_riesgo"], 99), x["dias_restantes"]))
    return resultado


def _obtener_documentos_pendientes_por_proceso(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
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
    return [
        {
            "proceso_id": item.proceso_id,
            "tipo_documento": item.tipo_documento,
            "estado": item.estado.value,
        }
        for item in items
    ]


def _obtener_grilla_seguimientos(
    db: Session, instructor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    query = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)

    procesos = query.all()
    grilla = []
    for p in procesos:
        for momento in MomentoReunion:
            reunion = db.query(ReunionSeguimiento).filter(
                ReunionSeguimiento.proceso_id == p.id,
                ReunionSeguimiento.momento == momento,
                ReunionSeguimiento.is_active == True
            ).first()
            estado = "NO_PROGRAMADO"
            fecha_prog = None
            fecha_real = None
            if reunion:
                fecha_prog = reunion.fecha_programada.date()
                if reunion.fecha_realizada:
                    estado = "REALIZADO"
                    fecha_real = reunion.fecha_realizada.date()
                else:
                    estado = "PENDIENTE"
            grilla.append({
                "proceso_id": p.id,
                "momento": momento.value,
                "estado": estado,
                "fecha_programada": fecha_prog,
                "fecha_realizada": fecha_real,
            })
    return grilla


def _contar_aprendices_sin_alternativa(db: Session) -> int:
    subquery = db.query(ProcesoEtapaProductiva.aprendiz_id).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).subquery()
    return db.query(func.count(Usuario.id)).filter(
        Usuario.rol_id == 4,
        Usuario.is_active == True,
        Usuario.id.notin_(subquery)
    ).scalar() or 0


def _contar_aprendices_pendientes_iniciar(db: Session) -> int:
    hoy = date.today()
    subquery = db.query(ProcesoEtapaProductiva.aprendiz_id).filter(
        ProcesoEtapaProductiva.fecha_inicio > hoy,
        ProcesoEtapaProductiva.is_active == True
    ).subquery()
    return db.query(func.count(Usuario.id)).filter(
        Usuario.rol_id == 4,
        Usuario.is_active == True,
        Usuario.id.in_(subquery)
    ).scalar() or 0


def _contar_seguimientos_pendientes(db: Session, instructor_id: Optional[int] = None) -> int:
    query = db.query(func.count(ReunionSeguimiento.id)).filter(
        ReunionSeguimiento.fecha_programada < datetime.utcnow(),
        ReunionSeguimiento.fecha_realizada.is_(None),
        ReunionSeguimiento.is_active == True
    ).join(
        ProcesoEtapaProductiva,
        ReunionSeguimiento.proceso_id == ProcesoEtapaProductiva.id
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)
    return query.scalar() or 0


def _contar_medidas_formativas_pendientes(db: Session, instructor_id: Optional[int] = None) -> int:
    query = db.query(func.count(MedidasFormativasProceso.id)).filter(
        MedidasFormativasProceso.llamado_atencion_estado == EstadoMedidaFormativa.PENDIENTE,
        MedidasFormativasProceso.is_active == True
    ).join(
        ProcesoEtapaProductiva,
        MedidasFormativasProceso.proceso_id == ProcesoEtapaProductiva.id
    )
    if instructor_id:
        query = query.filter(ProcesoEtapaProductiva.instructor_id == instructor_id)
    return query.scalar() or 0


def _calcular_cumplimiento_por_programa(db: Session) -> List[Dict[str, Any]]:
    programas = db.query(ProgramaFormacion).filter(ProgramaFormacion.is_active == True).all()
    resultado = []
    for prog in programas:
        total = db.query(func.count(ProcesoEtapaProductiva.id)).join(
            Ficha, ProcesoEtapaProductiva.ficha_id == Ficha.id
        ).filter(Ficha.programa_id == prog.id, ProcesoEtapaProductiva.is_active == True).scalar() or 0
        completados = db.query(func.count(ProcesoEtapaProductiva.id)).join(
            Ficha, ProcesoEtapaProductiva.ficha_id == Ficha.id
        ).filter(
            Ficha.programa_id == prog.id,
            ProcesoEtapaProductiva.estado == EstadoProceso.FINALIZADO,
            ProcesoEtapaProductiva.is_active == True
        ).scalar() or 0
        porcentaje = round((completados / total) * 100, 2) if total else 0
        resultado.append({
            "programa_id": prog.id,
            "programa_nombre": prog.nombre,
            "total_procesos": total,
            "completados": completados,
            "porcentaje": porcentaje,
        })
    return resultado


def _calcular_cumplimiento_por_instructor(db: Session) -> List[Dict[str, Any]]:
    instructores = db.query(Usuario).filter(
        Usuario.rol_id == 3,
        Usuario.is_active == True
    ).all()
    resultado = []
    for inst in instructores:
        total = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
            ProcesoEtapaProductiva.instructor_id == inst.id,
            ProcesoEtapaProductiva.is_active == True
        ).scalar() or 0
        completados = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
            ProcesoEtapaProductiva.instructor_id == inst.id,
            ProcesoEtapaProductiva.estado == EstadoProceso.FINALIZADO,
            ProcesoEtapaProductiva.is_active == True
        ).scalar() or 0
        porcentaje = round((completados / total) * 100, 2) if total else 0
        resultado.append({
            "instructor_id": inst.id,
            "instructor_nombre": f"{inst.nombre} {inst.apellido}",
            "total_procesos": total,
            "completados": completados,
            "porcentaje": porcentaje,
        })
    return resultado


# ================== Dashboards ==================

def get_dashboard_admin(db: Session) -> Dict[str, Any]:
    total_usuarios = db.query(func.count(Usuario.id)).filter(Usuario.is_active == True).scalar() or 0
    total_aprendices = db.query(func.count(Usuario.id)).filter(Usuario.rol_id == 4, Usuario.is_active == True).scalar() or 0
    total_instructores = db.query(func.count(Usuario.id)).filter(Usuario.rol_id == 3, Usuario.is_active == True).scalar() or 0
    total_fichas = db.query(func.count(Ficha.id)).filter(Ficha.is_active == True).scalar() or 0
    total_activos = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    total_finalizados = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.FINALIZADO,
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    pendientes_iniciar = _contar_aprendices_pendientes_iniciar(db)
    sin_alternativa = _contar_aprendices_sin_alternativa(db)
    seguimientos_pendientes = _contar_seguimientos_pendientes(db)
    procesos_riesgo = _obtener_procesos_riesgo(db)
    docs_pendientes = len(_obtener_documentos_pendientes_por_proceso(db))
    total_novedades = db.query(func.count(NovedadProceso.id)).filter(NovedadProceso.is_active == True).scalar() or 0
    cumplimiento_programa = _calcular_cumplimiento_por_programa(db)
    # Podría agregarse cumplimiento por instructor, pero DashboardAdmin lo incluye? Lo mantengo solo en coordinador.

    return {
        "total_usuarios_activos": total_usuarios,
        "total_aprendices_etapa_productiva": total_aprendices,
        "total_instructores": total_instructores,
        "total_fichas": total_fichas,
        "total_procesos_activos": total_activos,
        "total_procesos_finalizados": total_finalizados,
        "aprendices_pendientes_iniciar": pendientes_iniciar,
        "aprendices_sin_alternativa": sin_alternativa,
        "seguimientos_pendientes": seguimientos_pendientes,
        "procesos_en_riesgo": procesos_riesgo,
        "documentos_pendientes": docs_pendientes,
        "total_novedades": total_novedades,
        "cumplimiento_por_programa": cumplimiento_programa,
    }


def get_dashboard_coordinador(db: Session) -> Dict[str, Any]:
    total_fichas = db.query(func.count(Ficha.id)).filter(Ficha.is_active == True).scalar() or 0
    total_instructores = db.query(func.count(Usuario.id)).filter(Usuario.rol_id == 3, Usuario.is_active == True).scalar() or 0
    total_activos = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    total_pendientes = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.estado_sofia.in_(["PENDIENTE", "POR_EVALUAR"]),
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    alertas_criticas = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.fecha_fin <= date.today() + timedelta(days=30),
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0
    pendientes_iniciar = _contar_aprendices_pendientes_iniciar(db)
    sin_alternativa = _contar_aprendices_sin_alternativa(db)
    seguimientos_pendientes = _contar_seguimientos_pendientes(db)
    procesos_riesgo = _obtener_procesos_riesgo(db)
    docs_pendientes = len(_obtener_documentos_pendientes_por_proceso(db))
    medidas_pendientes = _contar_medidas_formativas_pendientes(db)

    return {
        "total_fichas_asignadas": total_fichas,
        "total_instructores_activos": total_instructores,
        "total_procesos_activos": total_activos,
        "total_procesos_pendientes": total_pendientes,
        "alertas_criticas": alertas_criticas,
        "aprendices_pendientes_iniciar": pendientes_iniciar,
        "aprendices_sin_alternativa": sin_alternativa,
        "seguimientos_pendientes": seguimientos_pendientes,
        "procesos_en_riesgo": procesos_riesgo,
        "documentos_pendientes": docs_pendientes,
        "medidas_formativas_pendientes": medidas_pendientes,
    }


def get_dashboard_instructor(db: Session, instructor_id: int) -> Dict[str, Any]:
    total_fichas = db.query(func.count(AsignacionInstructorFicha.id)).filter(
        AsignacionInstructorFicha.instructor_id == instructor_id,
        AsignacionInstructorFicha.estado_asignacion == "ACTIVA",
        AsignacionInstructorFicha.is_active == True
    ).scalar() or 0

    total_aprendices = db.query(func.count(ProcesoEtapaProductiva.id)).filter(
        ProcesoEtapaProductiva.instructor_id == instructor_id,
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).scalar() or 0

    total_bitacoras_pendientes = db.query(func.count(Bitacora.id)).join(
        ProcesoEtapaProductiva,
        Bitacora.proceso_id == ProcesoEtapaProductiva.id
    ).filter(
        ProcesoEtapaProductiva.instructor_id == instructor_id,
        Bitacora.estado == EstadoBitacora.ENVIADA,
        Bitacora.is_active == True
    ).scalar() or 0

    hoy = date.today()
    proximas_reuniones = db.query(func.count(ReunionSeguimiento.id)).join(
        ProcesoEtapaProductiva,
        ReunionSeguimiento.proceso_id == ProcesoEtapaProductiva.id
    ).filter(
        ProcesoEtapaProductiva.instructor_id == instructor_id,
        ReunionSeguimiento.fecha_programada.between(hoy, hoy + timedelta(days=30)),
        ReunionSeguimiento.fecha_realizada.is_(None),
        ReunionSeguimiento.is_active == True
    ).scalar() or 0

    procesos_riesgo = _obtener_procesos_riesgo(db, instructor_id=instructor_id)
    grilla = _obtener_grilla_seguimientos(db, instructor_id=instructor_id)
    docs_pendientes = len(_obtener_documentos_pendientes_por_proceso(db, instructor_id=instructor_id))
    seguimientos_pendientes = _contar_seguimientos_pendientes(db, instructor_id=instructor_id)
    medidas_pendientes = _contar_medidas_formativas_pendientes(db, instructor_id=instructor_id)

    return {
        "total_fichas_asignadas": total_fichas,
        "total_aprendices_cargo": total_aprendices,
        "total_bitacoras_pendientes": total_bitacoras_pendientes,
        "proximas_reuniones": proximas_reuniones,
        "procesos_en_riesgo": procesos_riesgo,
        "grilla_seguimientos": grilla,
        "documentos_pendientes": docs_pendientes,
        "seguimientos_pendientes": seguimientos_pendientes,
        "medidas_formativas_pendientes": medidas_pendientes,
    }

# ================== Dashboard Instructor ==================
def get_dashboard_instructor(db: Session, instructor_id: int):
    """
    Obtiene el dashboard del instructor con:
    - Total de aprendices asignados
    - Bitácoras pendientes de revisión
    - Reuniones de seguimiento próximas
    """
    from app.models import ProcesoEtapaProductiva, Bitacora, ReunionSeguimiento
    from app.models import EstadoBitacora, Usuario
    from datetime import date, timedelta
    
    # 1. Total de aprendices asignados (procesos activos)
    total_aprendices = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.instructor_id == instructor_id,
        ProcesoEtapaProductiva.estado == "ACTIVO",
        ProcesoEtapaProductiva.is_active == True
    ).count()
    
    # 2. Bitácoras pendientes de revisión (estado ENVIADA)
    bitacoras_pendientes = db.query(Bitacora).join(
        ProcesoEtapaProductiva, 
        ProcesoEtapaProductiva.id == Bitacora.proceso_id
    ).filter(
        ProcesoEtapaProductiva.instructor_id == instructor_id,
        Bitacora.estado == EstadoBitacora.ENVIADA,
        Bitacora.is_active == True
    ).count()
    
    # 3. Reuniones de seguimiento próximas (próximos 7 días)
    hoy = date.today()
    siguiente_semana = hoy + timedelta(days=7)
    
    reuniones_proximas = db.query(ReunionSeguimiento).join(
        ProcesoEtapaProductiva, 
        ProcesoEtapaProductiva.id == ReunionSeguimiento.proceso_id
    ).filter(
        ProcesoEtapaProductiva.instructor_id == instructor_id,
        ReunionSeguimiento.fecha_programada >= hoy,
        ReunionSeguimiento.fecha_programada <= siguiente_semana,
        ReunionSeguimiento.is_active == True
    ).count()
    
    # Obtener nombre del instructor
    instructor = db.query(Usuario).filter(Usuario.id == instructor_id).first()
    
    return {
        "total_aprendices": total_aprendices,
        "bitacoras_pendientes": bitacoras_pendientes,
        "reuniones_proximas": reuniones_proximas,
        "instructor_id": instructor_id,
        "instructor_nombre": instructor.nombre if instructor else None
    }