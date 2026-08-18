from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.core.constants import Roles, RolesPermisos
from app.models import Usuario, Ficha, ProcesoEtapaProductiva
from app.modules.busqueda import crud
from app.modules.busqueda.schemas import BusquedaResponse, ResultadoBusqueda

router = APIRouter(prefix="/busqueda", tags=["busqueda"])


@router.get("", response_model=BusquedaResponse)
def busqueda_unificada(
    q: str = Query(..., min_length=3, description="Texto a buscar"),
    ambito: Optional[str] = Query(
        None,
        pattern="^(usuarios|instructores|programas|fichas|procesos)$",
        description="Ámbito específico de búsqueda"
    ),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """
    Búsqueda unificada por texto.
    - Admin/Coordinador/Apoyo: acceso global.
    - Instructor: solo en sus procesos, fichas asignadas y aprendices relacionados.
    - Aprendiz: no tiene acceso a esta búsqueda global.
    """
    instructor_id = None
    aprendiz_id = None

    if current_user.rol_id == Roles.INSTRUCTOR:
        instructor_id = current_user.id

    # Aprendiz no debería llegar aquí por el require_role, pero aseguramos
    if current_user.rol_id == Roles.APRENDIZ:
        aprendiz_id = current_user.id

    resultados: List[ResultadoBusqueda] = []

    # Usuarios
    if ambito is None or ambito == "usuarios":
        # Para instructor se restringe a sus aprendices
        usuarios = crud.buscar_usuarios(
            db, q,
            instructor_id=instructor_id,
            rol_id=None if current_user.rol_id != Roles.INSTRUCTOR else 4
        )
        for u in usuarios:
            resultados.append(ResultadoBusqueda(
                tipo="usuario",
                id=u.id,
                titulo=f"{u.nombre} {u.apellido}",
                subtitulo=f"Rol ID: {u.rol_id}",
                descripcion=u.email,
            ))

    # Instructores
    if ambito is None or ambito == "instructores":
        # Solo admin/coordinador pueden buscar instructores
        if current_user.rol_id in (Roles.ADMIN, Roles.COORDINADOR):
            instructores = crud.buscar_instructores(db, q)
            for i in instructores:
                resultados.append(ResultadoBusqueda(
                    tipo="instructor",
                    id=i.id,
                    titulo=f"{i.nombre} {i.apellido}",
                    subtitulo="Instructor",
                    descripcion=i.email,
                ))

    # Programas
    if ambito is None or ambito == "programas":
        # Instructor no puede buscar programas globales
        if current_user.rol_id != Roles.INSTRUCTOR:
            programas = crud.buscar_programas(db, q)
            for p in programas:
                resultados.append(ResultadoBusqueda(
                    tipo="programa",
                    id=p.id,
                    titulo=p.nombre,
                    subtitulo=f"Código: {p.codigo}",
                    descripcion=p.descripcion,
                ))

    # Fichas
    if ambito is None or ambito == "fichas":
        if current_user.rol_id != Roles.APRENDIZ:
            fichas = crud.buscar_fichas(
                db, q,
                instructor_id=instructor_id
            )
            for f in fichas:
                resultados.append(ResultadoBusqueda(
                    tipo="ficha",
                    id=f.id,
                    titulo=f"Ficha {f.numero_ficha}",
                    subtitulo=f"Programa ID: {f.programa_id}",
                    descripcion=f"Inicio: {f.fecha_inicio} - Fin: {f.fecha_fin}",
                ))

    # Procesos
    if ambito is None or ambito == "procesos":
        procesos = crud.buscar_procesos(
            db, q,
            instructor_id=instructor_id,
            aprendiz_id=aprendiz_id
        )
        for p in procesos:
            aprendiz = db.query(Usuario).filter(Usuario.id == p.aprendiz_id).first()
            ficha = db.query(Ficha).filter(Ficha.id == p.ficha_id).first()
            resultados.append(ResultadoBusqueda(
                tipo="proceso",
                id=p.id,
                titulo=f"Proceso {p.id}",
                subtitulo=f"Aprendiz: {aprendiz.nombre} {aprendiz.apellido}" if aprendiz else "",
                descripcion=f"Ficha: {ficha.numero_ficha if ficha else ''} | Estado: {p.estado.value}",
            ))

    return BusquedaResponse(total=len(resultados), resultados=resultados)