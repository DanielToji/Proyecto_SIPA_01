from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.constants import Roles
from app.models import (
    NotificacionMensaje,
    ProcesoEtapaProductiva,
    Usuario,
    ReunionSeguimiento,
    ChecklistDocumentoProceso,
    EstadoEnvioEmail,
    EstadoProceso,
    EstadoDocumento,
    MomentoReunion,
    EstadoSofia,
)
from app.modules.notificaciones import crud


def _obtener_instructores_activos(db: Session) -> list[Usuario]:
    return db.query(Usuario).filter(
        Usuario.rol_id == Roles.INSTRUCTOR,
        Usuario.is_active == True
    ).all()


def _obtener_coordinadores_activos(db: Session) -> list[Usuario]:
    return db.query(Usuario).filter(
        Usuario.rol_id == Roles.COORDINADOR,
        Usuario.is_active == True
    ).all()


# ============================================================
# RF-09: Alertas automáticas
# ============================================================

def generar_alertas_sin_alternativa(db: Session) -> list[NotificacionMensaje]:
    """
    Alerta: aprendices activos que no tienen un proceso activo asociado.
    Notifica a todos los coordinadores activos.
    """
    subquery = db.query(ProcesoEtapaProductiva.aprendiz_id).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).subquery()

    aprendices_sin_proceso = db.query(Usuario).filter(
        Usuario.rol_id == Roles.APRENDIZ,
        Usuario.is_active == True,
        Usuario.id.notin_(subquery)
    ).all()

    if not aprendices_sin_proceso:
        return []

    cuerpo = "Aprendices activos sin proceso de etapa productiva definido:\n\n"
    for aprendiz in aprendices_sin_proceso:
        cuerpo += f"- {aprendiz.nombre} {aprendiz.apellido} (doc: {aprendiz.documento_identidad or 'N/A'})\n"

    asunto = f"Alerta: {len(aprendices_sin_proceso)} aprendices sin alternativa definida"
    creadas = []
    for coordinador in _obtener_coordinadores_activos(db):
        nueva = crud._crear_notificacion_si_no_existe(
            db,
            destinatario_id=coordinador.id,
            asunto=asunto,
            cuerpo=cuerpo,
            remitente_usuario_id=None,
        )
        if nueva:
            creadas.append(nueva)
    return creadas


def generar_alertas_momentos_vencidos(db: Session) -> list[NotificacionMensaje]:
    """
    Alerta: reuniones de seguimiento con fecha_programada vencida y no realizadas.
    Notifica al instructor asignado a cada proceso.
    """
    hoy = datetime.utcnow()
    vencidas = db.query(ReunionSeguimiento).filter(
        ReunionSeguimiento.fecha_programada < hoy,
        ReunionSeguimiento.fecha_realizada.is_(None),
        ReunionSeguimiento.is_active == True
    ).all()

    if not vencidas:
        return []

    # Agrupar por instructor para evitar spam
    instructores = {}
    for reunion in vencidas:
        proceso = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.id == reunion.proceso_id
        ).first()
        if not proceso:
            continue
        instructor_id = proceso.instructor_id
        if instructor_id not in instructores:
            instructores[instructor_id] = []
        instructores[instructor_id].append({
            "proceso_id": proceso.id,
            "momento": reunion.momento.value,
            "fecha_programada": reunion.fecha_programada.date(),
        })

    creadas = []
    for instructor_id, detalles in instructores.items():
        cuerpo = "Reuniones de seguimiento vencidas sin realizar:\n\n"
        for det in detalles:
            cuerpo += (
                f"- Proceso {det['proceso_id']}, Momento: {det['momento']}, "
                f"Programada: {det['fecha_programada']}\n"
            )
        asunto = f"Alerta: {len(detalles)} reuniones de seguimiento vencidas"
        nueva = crud._crear_notificacion_si_no_existe(
            db,
            destinatario_id=instructor_id,
            asunto=asunto,
            cuerpo=cuerpo,
            remitente_usuario_id=None,
        )
        if nueva:
            creadas.append(nueva)
    return creadas


def generar_alertas_documentacion_pendiente(db: Session) -> list[NotificacionMensaje]:
    """
    Alerta: checklist de documentos pendientes por proceso.
    Notifica al instructor del proceso.
    """
    pendientes = db.query(ChecklistDocumentoProceso).filter(
        ChecklistDocumentoProceso.estado == EstadoDocumento.PENDIENTE,
        ChecklistDocumentoProceso.is_active == True
    ).join(
        ProcesoEtapaProductiva,
        ChecklistDocumentoProceso.proceso_id == ProcesoEtapaProductiva.id
    ).all()

    if not pendientes:
        return []

    instructores = {}
    for item in pendientes:
        proceso = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.id == item.proceso_id
        ).first()
        if not proceso:
            continue
        instructor_id = proceso.instructor_id
        if instructor_id not in instructores:
            instructores[instructor_id] = []
        instructores[instructor_id].append({
            "proceso_id": proceso.id,
            "tipo_documento": item.tipo_documento,
        })

    creadas = []
    for instructor_id, detalles in instructores.items():
        cuerpo = "Documentos pendientes en checklist:\n\n"
        for det in detalles:
            cuerpo += f"- Proceso {det['proceso_id']}: {det['tipo_documento']}\n"
        asunto = f"Alerta: {len(detalles)} documentos pendientes"
        nueva = crud._crear_notificacion_si_no_existe(
            db,
            destinatario_id=instructor_id,
            asunto=asunto,
            cuerpo=cuerpo,
            remitente_usuario_id=None,
        )
        if nueva:
            creadas.append(nueva)
    return creadas


def generar_alertas_proxima_finalizacion(db: Session) -> list[NotificacionMensaje]:
    """
    Alerta: procesos activos cuya fecha de finalización está próxima (<= 15 días).
    Notifica al instructor del proceso.
    """
    hoy = date.today()
    limite = hoy + timedelta(days=15)
    procesos = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True,
        ProcesoEtapaProductiva.fecha_fin <= limite,
        ProcesoEtapaProductiva.fecha_fin >= hoy,
    ).all()

    if not procesos:
        return []

    instructores = {}
    for proceso in procesos:
        if proceso.instructor_id not in instructores:
            instructores[proceso.instructor_id] = []
        instructores[proceso.instructor_id].append({
            "proceso_id": proceso.id,
            "aprendiz_id": proceso.aprendiz_id,
            "fecha_fin": proceso.fecha_fin,
        })

    creadas = []
    for instructor_id, detalles in instructores.items():
        cuerpo = "Procesos próximos a finalizar:\n\n"
        for det in detalles:
            cuerpo += f"- Proceso {det['proceso_id']} (Aprendiz {det['aprendiz_id']}) finaliza el {det['fecha_fin']}\n"
        asunto = f"Alerta: {len(detalles)} procesos próximos a finalizar"
        nueva = crud._crear_notificacion_si_no_existe(
            db,
            destinatario_id=instructor_id,
            asunto=asunto,
            cuerpo=cuerpo,
            remitente_usuario_id=None,
        )
        if nueva:
            creadas.append(nueva)
    return creadas


def generar_alertas_evaluacion_pendiente(db: Session) -> list[NotificacionMensaje]:
    """
    Alerta: procesos con los tres momentos completados pero sin evaluación final.
    Notifica al instructor del proceso.
    """
    procesos_activos = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True,
        ProcesoEtapaProductiva.estado_sofia.in_([EstadoSofia.PENDIENTE, EstadoSofia.POR_EVALUAR])
    ).all()

    if not procesos_activos:
        return []

    instructores = {}
    for proceso in procesos_activos:
        # Verificar que tenga las 3 reuniones realizadas
        reuniones_realizadas = db.query(ReunionSeguimiento).filter(
            ReunionSeguimiento.proceso_id == proceso.id,
            ReunionSeguimiento.fecha_realizada.isnot(None),
            ReunionSeguimiento.is_active == True
        ).count()
        if reuniones_realizadas == 3:
            if proceso.instructor_id not in instructores:
                instructores[proceso.instructor_id] = []
            instructores[proceso.instructor_id].append({
                "proceso_id": proceso.id,
                "aprendiz_id": proceso.aprendiz_id,
            })

    if not instructores:
        return []

    creadas = []
    for instructor_id, detalles in instructores.items():
        cuerpo = "Procesos con seguimiento completo pendientes de evaluación final:\n\n"
        for det in detalles:
            cuerpo += f"- Proceso {det['proceso_id']} (Aprendiz {det['aprendiz_id']})\n"
        asunto = f"Alerta: {len(detalles)} evaluaciones finales pendientes"
        nueva = crud._crear_notificacion_si_no_existe(
            db,
            destinatario_id=instructor_id,
            asunto=asunto,
            cuerpo=cuerpo,
            remitente_usuario_id=None,
        )
        if nueva:
            creadas.append(nueva)
    return creadas


def generar_todas_las_alertas(db: Session) -> list[NotificacionMensaje]:
    """Ejecuta todas las reglas de alerta y retorna las notificaciones creadas."""
    alertas = []
    alertas.extend(generar_alertas_sin_alternativa(db))
    alertas.extend(generar_alertas_momentos_vencidos(db))
    alertas.extend(generar_alertas_documentacion_pendiente(db))
    alertas.extend(generar_alertas_proxima_finalizacion(db))
    alertas.extend(generar_alertas_evaluacion_pendiente(db))
    return alertas