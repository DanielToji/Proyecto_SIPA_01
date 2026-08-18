from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import Roles, RolesPermisos
from app.models import (
    Usuario,
    ProcesoEtapaProductiva,
    ReunionSeguimiento,
    MomentoReunion,
    EvidenciaArchivo,
)
from app.modules.seguimientos import crud, schemas

router = APIRouter(prefix="/seguimientos", tags=["seguimientos"])


@router.post("", response_model=schemas.ReunionSeguimientoOut, status_code=status.HTTP_201_CREATED)
def crear_reunion(
    reunion: schemas.ReunionSeguimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea una reunión de seguimiento (momento F023) para un proceso.
    - Admin y Coordinador pueden crear cualquier reunión.
    - Instructor puede crearla solo si es el instructor asignado al proceso.
    """
    # Validar proceso activo
    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == reunion.proceso_id,
        ProcesoEtapaProductiva.is_active == True
    ).first()
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Validar instructor
    instructor = db.query(Usuario).filter(
        Usuario.id == reunion.instructor_id,
        Usuario.rol_id == Roles.INSTRUCTOR,
        Usuario.is_active == True
    ).first()
    if not instructor:
        raise HTTPException(status_code=400, detail="El usuario no es un instructor activo")

    # Verificar permisos: instructor solo si coincide con el proceso
    if current_user.rol_id == Roles.INSTRUCTOR:
        if proceso.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")

    # Validar que no exista una reunión para el mismo proceso y momento
    existente = crud.get_reunion_by_proceso_momento(
        db, reunion.proceso_id, reunion.momento
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una reunión programada para ese momento del proceso"
        )

    data = reunion.model_dump()
    data["is_active"] = True
    nueva_reunion = crud.create_reunion(db, data)
    return nueva_reunion


@router.get("", response_model=list[schemas.ReunionSeguimientoOut])
def listar_reuniones(
    proceso_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    momento: Optional[MomentoReunion] = None,
    solo_activas: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista reuniones de seguimiento con filtros.
    - Admin/Coordinador ven todas.
    - Instructor solo ve las de sus procesos asignados.
    - Aprendiz solo ve las de su propio proceso.
    """
    proceso_ids = None

    if current_user.rol_id == Roles.INSTRUCTOR:
        # Obtener los procesos asignados al instructor
        procesos = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.instructor_id == current_user.id,
            ProcesoEtapaProductiva.is_active == True
        ).all()
        proceso_ids = [p.id for p in procesos]
        if not proceso_ids:
            return []
    elif current_user.rol_id == Roles.APRENDIZ:
        # Obtener solo los procesos del aprendiz
        procesos = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.aprendiz_id == current_user.id,
            ProcesoEtapaProductiva.is_active == True
        ).all()
        proceso_ids = [p.id for p in procesos]
        if not proceso_ids:
            return []

    # Si se especifica proceso_id, y el usuario no tiene permiso, validar
    if proceso_id and current_user.rol_id in (Roles.INSTRUCTOR, Roles.APRENDIZ):
        if proceso_id not in proceso_ids:
            raise HTTPException(status_code=403, detail="No autorizado para ver ese proceso")

    return crud.list_reuniones(
        db,
        proceso_id=proceso_id,
        proceso_ids=proceso_ids,
        instructor_id=instructor_id,
        momento=momento,
        solo_activas=solo_activas,
        skip=skip,
        limit=limit,
    )


@router.get("/vencidas", response_model=list[schemas.ReunionSeguimientoOut])
def listar_reuniones_vencidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SEGUIMIENTO))
):
    """
    Lista reuniones vencidas (fecha_programada pasada y no realizada).
    RF-09: Momentos vencidos.
    - Admin/Coordinador: todas.
    - Instructor: solo las de sus procesos asignados.
    """
    instructor_id = None
    proceso_ids = None

    if current_user.rol_id == Roles.INSTRUCTOR:
        instructor_id = current_user.id
        procesos = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.instructor_id == instructor_id,
            ProcesoEtapaProductiva.is_active == True
        ).all()
        proceso_ids = [p.id for p in procesos]
        if not proceso_ids:
            return []

    return crud.list_reuniones_vencidas(
        db,
        instructor_id=instructor_id,
        proceso_ids=proceso_ids,
    )


@router.get("/{reunion_id}", response_model=schemas.ReunionSeguimientoOut)
def obtener_reunion(
    reunion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una reunión por ID con control de acceso."""
    reunion = crud.get_reunion(db, reunion_id)
    if not reunion:
        raise HTTPException(status_code=404, detail="Reunión no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == reunion.proceso_id
    ).first()

    if current_user.rol_id == Roles.INSTRUCTOR and reunion.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta reunión")
    if current_user.rol_id == Roles.APRENDIZ:
        if not proceso or proceso.aprendiz_id != current_user.id:
            raise HTTPException(status_code=403, detail="No autorizado para ver esta reunión")

    return reunion


@router.put("/{reunion_id}", response_model=schemas.ReunionSeguimientoOut)
def actualizar_reunion(
    reunion_id: int,
    datos: schemas.ReunionSeguimientoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza una reunión de seguimiento.
    - Admin/Coordinador pueden actualizar cualquier reunión.
    - Instructor solo si es el asignado al proceso.
    Valida reglas de fechas y evidencia antes de persistir.
    """
    reunion = crud.get_reunion(db, reunion_id)
    if not reunion:
        raise HTTPException(status_code=404, detail="Reunión no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == reunion.proceso_id
    ).first()

    if current_user.rol_id == Roles.INSTRUCTOR:
        if not proceso or proceso.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")

    # Validar instructor si se cambia
    if datos.instructor_id:
        instructor = db.query(Usuario).filter(
            Usuario.id == datos.instructor_id,
            Usuario.rol_id == Roles.INSTRUCTOR,
            Usuario.is_active == True
        ).first()
        if not instructor:
            raise HTTPException(status_code=400, detail="El usuario no es un instructor activo")

    # Obtener fechas resultantes
    nueva_fecha_programada = datos.fecha_programada if datos.fecha_programada else reunion.fecha_programada
    nueva_fecha_realizada = datos.fecha_realizada if datos.fecha_realizada else reunion.fecha_realizada

    # Validar fecha_realizada >= fecha_programada
    if nueva_fecha_realizada and nueva_fecha_realizada < nueva_fecha_programada:
        raise HTTPException(
            status_code=400,
            detail="La fecha realizada no puede ser anterior a la fecha programada"
        )

    # Validar que si se marca realizada, exista evidencia (archivo o URL)
    if nueva_fecha_realizada:
        evidencia_id = datos.evidencia_archivo_id if datos.evidencia_archivo_id else reunion.evidencia_archivo_id
        url = datos.archivo_f023_url if datos.archivo_f023_url else reunion.archivo_f023_url
        if not evidencia_id and not url:
            raise HTTPException(
                status_code=400,
                detail="Para registrar una reunión realizada debe adjuntar evidencia (archivo o URL F023)"
            )

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_reunion(db, reunion, update_data)


@router.delete("/{reunion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_reunion(
    reunion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Desactiva una reunión (soft delete).
    - Admin/Coordinador pueden eliminar cualquier reunión.
    - Instructor solo si es el asignado al proceso.
    """
    reunion = crud.get_reunion(db, reunion_id)
    if not reunion:
        raise HTTPException(status_code=404, detail="Reunión no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == reunion.proceso_id
    ).first()

    if current_user.rol_id == Roles.INSTRUCTOR:
        if not proceso or proceso.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")

    crud.soft_delete_reunion(db, reunion)
    return None