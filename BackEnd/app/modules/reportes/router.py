from typing import Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import Roles
from app.models import (
    Usuario,
    ProcesoEtapaProductiva,
    Ficha,
    ProgramaFormacion,
    AsignacionInstructorFicha,
    ReunionSeguimiento,
    Bitacora,
)
from app.modules.reportes import crud, schemas

# 🔥 FIX: prefijo agregado para que las rutas sean /reportes/...
router = APIRouter(prefix="/reportes", tags=["Reportes"])


# ============================================================
# ENDPOINTS EXISTENTES (descargas Excel/PDF)
# ============================================================

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR)),
):
    """Datos del dashboard para coordinadores."""
    return crud.get_dashboard_data(db)


@router.get("/estado-aprendices")
def reporte_estado_aprendices(
    ficha_id: Optional[int] = None,
    programa_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR)),
):
    """Reporte de estado de aprendices."""
    return crud.get_estado_aprendices(db, ficha_id=ficha_id, programa_id=programa_id)


@router.get("/bitacoras")
def reporte_bitacoras(
    ficha_id: Optional[int] = None,
    aprendiz_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR)),
):
    """Reporte de bitácoras."""
    return crud.get_reporte_bitacoras(db, ficha_id=ficha_id, aprendiz_id=aprendiz_id)


@router.get("/seguimientos")
def reporte_seguimientos(
    ficha_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR)),
):
    """Reporte de seguimientos."""
    return crud.get_reporte_seguimientos(db, ficha_id=ficha_id)


# ============================================================
# NUEVOS: ENDPOINTS JSON PARA EL FRONTEND
# ============================================================

@router.get("/fichas-json")
def reporte_fichas_json(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR)),
):
    """
    Lista todas las fichas con instructor, aprendices, fechas y avance.
    Formato JSON para el frontend.
    """
    fichas = db.query(Ficha).filter(Ficha.is_active == True).all()

    resultado = []
    for ficha in fichas:
        # Instructor asignado
        asignacion = (
            db.query(AsignacionInstructorFicha)
            .filter(
                AsignacionInstructorFicha.ficha_id == ficha.id,
                AsignacionInstructorFicha.is_active == True,
                AsignacionInstructorFicha.estado_asignacion == "ACTIVA",
            )
            .first()
        )
        instructor_nombre = ""
        if asignacion:
            instr = db.query(Usuario).filter(Usuario.id == asignacion.instructor_id).first()
            if instr:
                instructor_nombre = f"{instr.nombre} {instr.apellido}"

        # Aprendices de la ficha
        procesos = (
            db.query(ProcesoEtapaProductiva)
            .filter(
                ProcesoEtapaProductiva.ficha_id == ficha.id,
                ProcesoEtapaProductiva.is_active == True,
            )
            .all()
        )

        # Programa
        programa = db.query(ProgramaFormacion).filter(
            ProgramaFormacion.id == ficha.programa_id
        ).first()

        resultado.append({
            "id": ficha.id,
            "numero_ficha": ficha.numero_ficha,
            "programa": programa.nombre if programa else "",
            "instructor": instructor_nombre or "Sin asignar",
            "aprendices": len(procesos),
            "fecha_inicio": ficha.fecha_inicio.isoformat() if ficha.fecha_inicio else None,
            "fecha_fin": ficha.fecha_fin.isoformat() if ficha.fecha_fin else None,
            "avance": 0,
        })

    return resultado


@router.get("/ficha-detalle/{ficha_id}")
def reporte_ficha_detalle(
    ficha_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR)),
):
    """
    Detalle de una ficha con sus aprendices, momentos, bitácoras y avance.
    """
    ficha = db.query(Ficha).filter(Ficha.id == ficha_id).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")

    # Programa
    programa = db.query(ProgramaFormacion).filter(
        ProgramaFormacion.id == ficha.programa_id
    ).first()

    # Instructor
    asignacion = (
        db.query(AsignacionInstructorFicha)
        .filter(
            AsignacionInstructorFicha.ficha_id == ficha_id,
            AsignacionInstructorFicha.is_active == True,
        )
        .first()
    )
    instructor_nombre = ""
    if asignacion:
        instr = db.query(Usuario).filter(Usuario.id == asignacion.instructor_id).first()
        if instr:
            instructor_nombre = f"{instr.nombre} {instr.apellido}"

    # Procesos (aprendices)
    procesos = (
        db.query(ProcesoEtapaProductiva)
        .filter(
            ProcesoEtapaProductiva.ficha_id == ficha_id,
            ProcesoEtapaProductiva.is_active == True,
        )
        .all()
    )

    aprendices_data = []
    for p in procesos:
        # Momentos (reuniones)
        reuniones = (
            db.query(ReunionSeguimiento)
            .filter(
                ReunionSeguimiento.proceso_id == p.id,
                ReunionSeguimiento.is_active == True,
            )
            .all()
        )
        momentos = {"momento1": "Pendiente", "momento2": "Pendiente", "momento3": "Pendiente"}
        completados = 0
        for r in reuniones:
            if r.fecha_realizada:
                completados += 1
                momento_val = r.momento.value if hasattr(r.momento, 'value') else str(r.momento)
                if "1" in momento_val:
                    momentos["momento1"] = "Completado"
                elif "2" in momento_val:
                    momentos["momento2"] = "Completado"
                elif "3" in momento_val:
                    momentos["momento3"] = "Completado"

        # Bitácoras
        bitacoras = (
            db.query(Bitacora)
            .filter(Bitacora.proceso_id == p.id, Bitacora.is_active == True)
            .all()
        )
        bitacoras_data = {"bimestre1": "Pendiente", "bimestre2": "Pendiente", "bimestre3": "Pendiente"}
        for b in bitacoras:
            idx = b.numero_bitacora
            estado_val = b.estado.value if hasattr(b.estado, 'value') else str(b.estado)
            if idx == 1:
                bitacoras_data["bimestre1"] = estado_val
            elif idx == 2:
                bitacoras_data["bimestre2"] = estado_val
            elif idx == 3:
                bitacoras_data["bimestre3"] = estado_val

        # Avance = % momentos completados
        avance = round((completados / 3) * 100, 0)

        # Estado
        estado_val = p.estado.value if hasattr(p.estado, 'value') else str(p.estado)

        aprendices_data.append({
            "id": p.id,
            "aprendiz_id": p.aprendiz_id,
            "nombre": p.aprendiz_nombre or "Sin nombre",
            "documento": p.aprendiz_documento or "—",
            "email": p.aprendiz_email or "—",
            "telefono": p.aprendiz_telefono or "—",
            "empresa": p.empresa_nombre or "Sin asignar",
            "arl": p.arl or "—",
            "estado": "Activo" if estado_val == "ACTIVO" else estado_val,
            "fechaInicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
            "fechaFin": p.fecha_fin.isoformat() if p.fecha_fin else None,
            "momentos": momentos,
            "bitacoras": bitacoras_data,
            "avance": avance,
        })

    return {
        "id": ficha.id,
        "numero_ficha": ficha.numero_ficha,
        "programa": programa.nombre if programa else "",
        "instructor": instructor_nombre or "Sin asignar",
        "aprendices": aprendices_data,
    }


    # ============================================================
# MOMENTOS DE SEGUIMIENTO (Reuniones por proceso)
# ============================================================

@router.get("/momentos")
def reporte_momentos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR, Roles.INSTRUCTOR)),
):
    """
    Devuelve los 3 momentos (M1, M2, M3) con sus fichas y aprendices,
    basado en la tabla reuniones_seguimiento.
    """
    from app.models import (
        ReunionSeguimiento,
        ProcesoEtapaProductiva,
        Ficha,
        ProgramaFormacion,
        Usuario,
        AsignacionInstructorFicha,
    )

    MOMENTOS_CONFIG = [
        {
            "id": 1,
            "titulo": "Momento 1",
            "descripcion": "Inducción y Diagnóstico Inicial",
            "icono": "fa-flag",
            "color": "#3ca203",
            "momento_db": "MOMENTO_1_INICIAL",
        },
        {
            "id": 2,
            "titulo": "Momento 2",
            "descripcion": "Ejecución y Seguimiento",
            "icono": "fa-play-circle",
            "color": "#0ea5e9",
            "momento_db": "MOMENTO_2_PARCIAL",
        },
        {
            "id": 3,
            "titulo": "Momento 3",
            "descripcion": "Evaluación y Cierre",
            "icono": "fa-flag-checkered",
            "color": "#8b5cf6",
            "momento_db": "MOMENTO_3_FINAL",
        },
    ]

    resultado = []

    for config in MOMENTOS_CONFIG:
        # Buscar todas las reuniones de este momento
        reuniones = (
            db.query(ReunionSeguimiento)
            .filter(
                ReunionSeguimiento.momento == config["momento_db"],
                ReunionSeguimiento.is_active == True,
            )
            .all()
        )

        # Agrupar por ficha
        fichas_dict = {}

        for r in reuniones:
            proceso = db.query(ProcesoEtapaProductiva).filter(
                ProcesoEtapaProductiva.id == r.proceso_id
            ).first()
            if not proceso:
                continue

            ficha = db.query(Ficha).filter(Ficha.id == proceso.ficha_id).first()
            if not ficha:
                continue

            aprendiz = db.query(Usuario).filter(Usuario.id == proceso.aprendiz_id).first()
            if not aprendiz:
                continue

            # Instructor de la ficha
            asignacion = (
                db.query(AsignacionInstructorFicha)
                .filter(
                    AsignacionInstructorFicha.ficha_id == ficha.id,
                    AsignacionInstructorFicha.is_active == True,
                )
                .first()
            )
            instructor_nombre = "Sin asignar"
            if asignacion:
                instr = db.query(Usuario).filter(Usuario.id == asignacion.instructor_id).first()
                if instr:
                    instructor_nombre = f"{instr.nombre} {instr.apellido}"

            # Programa
            programa = db.query(ProgramaFormacion).filter(
                ProgramaFormacion.id == ficha.programa_id
            ).first()

            # Estado del aprendiz en este momento
            if r.fecha_realizada:
                estado = "Completado"
            elif r.fecha_programada:
                estado = "En proceso"
            else:
                estado = "Pendiente"

            fecha_str = ""
            if r.fecha_realizada:
                fecha_str = r.fecha_realizada.strftime("%d/%m/%Y")
            elif r.fecha_programada:
                fecha_str = r.fecha_programada.strftime("%d/%m/%Y")
            else:
                fecha_str = "-"

            aprendiz_data = {
                "id": r.id,
                "proceso_id": proceso.id,
                "nombre": f"{aprendiz.nombre} {aprendiz.apellido}",
                "estado": estado,
                "fecha": fecha_str,
                "observacion": r.observaciones or "Sin observaciones",
            }

            ficha_id_str = ficha.numero_ficha

            if ficha_id_str not in fichas_dict:
                fichas_dict[ficha_id_str] = {
                    "idFicha": ficha_id_str,
                    "programa": programa.nombre if programa else "Sin programa",
                    "instructor": instructor_nombre,
                    "aprendices": [],
                }

            fichas_dict[ficha_id_str]["aprendices"].append(aprendiz_data)

        resultado.append({
            "id": config["id"],
            "titulo": config["titulo"],
            "descripcion": config["descripcion"],
            "icono": config["icono"],
            "color": config["color"],
            "fichas": list(fichas_dict.values()),
        })

    return resultado


@router.get("/momentos/ficha/{ficha_id}")
def reporte_momentos_por_ficha(
    ficha_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR, Roles.INSTRUCTOR)),
):
    """
    Devuelve los aprendices de una ficha con su estado en cada momento.
    """
    from app.models import (
        ReunionSeguimiento,
        ProcesoEtapaProductiva,
        Ficha,
        ProgramaFormacion,
        Usuario,
        AsignacionInstructorFicha,
    )

    ficha = db.query(Ficha).filter(Ficha.id == ficha_id).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")

    procesos = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.ficha_id == ficha_id,
        ProcesoEtapaProductiva.is_active == True,
    ).all()

    resultado = []
    for p in procesos:
        aprendiz = db.query(Usuario).filter(Usuario.id == p.aprendiz_id).first()
        if not aprendiz:
            continue

        reuniones = db.query(ReunionSeguimiento).filter(
            ReunionSeguimiento.proceso_id == p.id,
            ReunionSeguimiento.is_active == True,
        ).all()

        momentos_data = {}
        for r in reuniones:
            momento_val = r.momento.value if hasattr(r.momento, "value") else str(r.momento)
            if r.fecha_realizada:
                estado = "Completado"
            elif r.fecha_programada:
                estado = "En proceso"
            else:
                estado = "Pendiente"

            fecha_str = ""
            if r.fecha_realizada:
                fecha_str = r.fecha_realizada.strftime("%d/%m/%Y")
            elif r.fecha_programada:
                fecha_str = r.fecha_programada.strftime("%d/%m/%Y")
            else:
                fecha_str = "-"

            momentos_data[momento_val] = {
                "id": r.id,
                "estado": estado,
                "fecha": fecha_str,
                "observacion": r.observaciones or "Sin observaciones",
            }

        resultado.append({
            "proceso_id": p.id,
            "aprendiz_id": p.aprendiz_id,
            "nombre": f"{aprendiz.nombre} {aprendiz.apellido}",
            "momentos": momentos_data,
        })

    return resultado