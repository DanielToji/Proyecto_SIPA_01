from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.core.constants import Roles, RolesPermisos
from app.models import Usuario
from app.modules.reportes import crud, services

router = APIRouter(prefix="/reportes", tags=["reportes"])


def _descargar(buffer, filename: str, content_type: str) -> StreamingResponse:
    return StreamingResponse(
        buffer,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _obtener_instructor_id(current_user: Usuario) -> Optional[int]:
    """Si el usuario es instructor, retorna su ID; si admin/coordinador, None."""
    if current_user.rol_id == Roles.INSTRUCTOR:
        return current_user.id
    return None


@router.get("/procesos-riesgo")
def reporte_procesos_riesgo(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """Reporte de procesos en riesgo."""
    instructor_id = _obtener_instructor_id(current_user)
    rows = crud.get_datos_procesos_riesgo(db, instructor_id)
    headers = ["proceso_id", "aprendiz", "documento", "ficha", "fecha_inicio", "fecha_fin", "dias_restantes", "riesgo", "instructor_id"]
    buffer, content_type, ext = services.generar_reporte("Procesos en Riesgo", headers, rows, formato)
    return _descargar(buffer, f"procesos_riesgo.{ext}", content_type)


@router.get("/documentos-pendientes")
def reporte_documentos_pendientes(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """Reporte de documentos pendientes."""
    instructor_id = _obtener_instructor_id(current_user)
    rows = crud.get_datos_documentos_pendientes(db, instructor_id)
    headers = ["proceso_id", "aprendiz", "documento", "ficha", "tipo_documento", "estado"]
    buffer, content_type, ext = services.generar_reporte("Documentos Pendientes", headers, rows, formato)
    return _descargar(buffer, f"documentos_pendientes.{ext}", content_type)


@router.get("/seguimientos")
def reporte_seguimientos(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """Reporte de seguimientos F023."""
    instructor_id = _obtener_instructor_id(current_user)
    rows = crud.get_datos_seguimientos(db, instructor_id)
    headers = ["proceso_id", "aprendiz", "ficha", "momento", "fecha_programada", "fecha_realizada", "estado"]
    buffer, content_type, ext = services.generar_reporte("Seguimientos F023", headers, rows, formato)
    return _descargar(buffer, f"seguimientos.{ext}", content_type)


@router.get("/bitacoras")
def reporte_bitacoras(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """Reporte de bitácoras F147."""
    instructor_id = _obtener_instructor_id(current_user)
    rows = crud.get_datos_bitacoras(db, instructor_id)
    headers = ["bitacora_id", "proceso_id", "aprendiz", "ficha", "numero_bitacora", "periodo", "titulo", "estado", "fecha_envio"]
    buffer, content_type, ext = services.generar_reporte("Bitácoras F147", headers, rows, formato)
    return _descargar(buffer, f"bitacoras.{ext}", content_type)


@router.get("/estado-aprendices")
def reporte_estado_aprendices(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """Reporte del estado general de aprendices."""
    instructor_id = _obtener_instructor_id(current_user)
    rows = crud.get_datos_estado_aprendices(db, instructor_id)
    headers = ["proceso_id", "aprendiz", "documento", "ficha", "programa", "modalidad", "empresa", "fecha_inicio", "fecha_fin", "estado", "estado_sofia"]
    buffer, content_type, ext = services.generar_reporte("Estado de Aprendices", headers, rows, formato)
    return _descargar(buffer, f"estado_aprendices.{ext}", content_type)


@router.get("/alternativas")
def reporte_alternativas(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """Reporte de alternativas de etapa productiva."""
    instructor_id = _obtener_instructor_id(current_user)
    rows = crud.get_datos_alternativas(db, instructor_id)
    headers = ["proceso_id", "aprendiz", "documento", "ficha", "programa", "modalidad", "empresa", "fecha_inicio", "fecha_fin", "estado", "estado_sofia"]
    buffer, content_type, ext = services.generar_reporte("Alternativas de Etapa Productiva", headers, rows, formato)
    return _descargar(buffer, f"alternativas.{ext}", content_type)


@router.get("/aprendices-sin-alternativa")
def reporte_aprendices_sin_alternativa(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Reporte de aprendices sin alternativa definida."""
    rows = crud.get_datos_aprendices_sin_alternativa(db)
    headers = ["aprendiz_id", "aprendiz", "documento", "email", "telefono"]
    buffer, content_type, ext = services.generar_reporte("Aprendices Sin Alternativa", headers, rows, formato)
    return _descargar(buffer, f"aprendices_sin_alternativa.{ext}", content_type)


@router.get("/evaluados-sin-evaluar")
def reporte_evaluados_sin_evaluar(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """Reporte de procesos evaluados y sin evaluar."""
    instructor_id = _obtener_instructor_id(current_user)
    rows = crud.get_datos_evaluados_sin_evaluar(db, instructor_id)
    headers = ["proceso_id", "aprendiz", "ficha", "nota_empresa", "nota_instructor", "estado_sofia", "evaluado"]
    buffer, content_type, ext = services.generar_reporte("Evaluados / Sin Evaluar", headers, rows, formato)
    return _descargar(buffer, f"evaluados_sin_evaluar.{ext}", content_type)


@router.get("/indicadores-gestion")
def reporte_indicadores_gestion(
    formato: str = Query("xlsx", pattern="^(xlsx|pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Reporte de indicadores de gestión."""
    rows = crud.get_datos_indicadores_gestion(db)
    headers = ["indicador", "valor"]
    buffer, content_type, ext = services.generar_reporte("Indicadores de Gestión", headers, rows, formato)
    return _descargar(buffer, f"indicadores_gestion.{ext}", content_type)  