from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import Roles, RolesPermisos
from app.models import Usuario, EstadoAsignacion
from app.modules.programas_fichas import crud, schemas

router = APIRouter(tags=["programas", "fichas", "asignaciones"])


# ================== Programas de Formación ==================
@router.post("/programas", response_model=schemas.ProgramaFormacionOut, status_code=status.HTTP_201_CREATED)
def crear_programa(
    programa: schemas.ProgramaFormacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RolesPermisos.ADMIN, RolesPermisos.COORDINADOR))
):
    """Crea un nuevo programa de formación."""
    if crud.get_programa_by_codigo(db, programa.codigo):
        raise HTTPException(status_code=400, detail="Ya existe un programa con ese código")
    return crud.create_programa(db, programa.model_dump())


@router.get("/programas", response_model=list[schemas.ProgramaFormacionOut])
def listar_programas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista programas de formación con búsqueda y paginación."""
    return crud.list_programas(db, skip=skip, limit=limit, solo_activos=solo_activos, search=search)


@router.get("/programas/{programa_id}", response_model=schemas.ProgramaFormacionOut)
def obtener_programa(
    programa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un programa por su ID."""
    programa = crud.get_programa(db, programa_id)
    if not programa:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    return programa


@router.put("/programas/{programa_id}", response_model=schemas.ProgramaFormacionOut)
def actualizar_programa(
    programa_id: int,
    datos: schemas.ProgramaFormacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Actualiza un programa de formación."""
    programa = crud.get_programa(db, programa_id)
    if not programa:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    if datos.codigo and datos.codigo != programa.codigo:
        if crud.get_programa_by_codigo(db, datos.codigo):
            raise HTTPException(status_code=400, detail="Ya existe un programa con ese código")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_programa(db, programa, update_data)


@router.delete("/programas/{programa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_programa(
    programa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Desactiva un programa de formación (soft delete)."""
    programa = crud.get_programa(db, programa_id)
    if not programa:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    crud.soft_delete_programa(db, programa)
    return None


# ================== Fichas ==================
@router.post("/fichas", response_model=schemas.FichaOut, status_code=status.HTTP_201_CREATED)
def crear_ficha(
    ficha: schemas.FichaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Crea una nueva ficha."""
    if crud.get_ficha_by_numero(db, ficha.numero_ficha):
        raise HTTPException(status_code=400, detail="Ya existe una ficha con ese número")

    if ficha.fecha_fin < ficha.fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha fin no puede ser anterior a la fecha inicio")

    programa = crud.get_programa(db, ficha.programa_id)
    if not programa or not programa.is_active:
        raise HTTPException(status_code=400, detail="El programa de formación no existe o está inactivo")

    return crud.create_ficha(db, ficha.model_dump())


@router.get("/fichas", response_model=list[schemas.FichaOut])
def listar_fichas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    programa_id: Optional[int] = None,
    search: Optional[str] = None,
    solo_activas: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista fichas con filtros por programa y número."""
    return crud.list_fichas(
        db, skip=skip, limit=limit,
        solo_activas=solo_activas,
        programa_id=programa_id,
        search=search
    )


@router.get("/fichas/{ficha_id}", response_model=schemas.FichaOut)
def obtener_ficha(
    ficha_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una ficha por su ID."""
    ficha = crud.get_ficha(db, ficha_id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")
    return ficha


@router.put("/fichas/{ficha_id}", response_model=schemas.FichaOut)
def actualizar_ficha(
    ficha_id: int,
    datos: schemas.FichaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Actualiza una ficha existente."""
    ficha = crud.get_ficha(db, ficha_id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")

    if datos.numero_ficha and datos.numero_ficha != ficha.numero_ficha:
        if crud.get_ficha_by_numero(db, datos.numero_ficha):
            raise HTTPException(status_code=400, detail="Ya existe una ficha con ese número")

    if datos.programa_id:
        programa = crud.get_programa(db, datos.programa_id)
        if not programa or not programa.is_active:
            raise HTTPException(status_code=400, detail="El programa de formación no existe o está inactivo")

    # Validar fechas si se actualizan parcialmente
    nueva_fecha_inicio = datos.fecha_inicio if datos.fecha_inicio else ficha.fecha_inicio
    nueva_fecha_fin = datos.fecha_fin if datos.fecha_fin else ficha.fecha_fin
    if nueva_fecha_fin < nueva_fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha fin no puede ser anterior a la fecha inicio")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_ficha(db, ficha, update_data)


@router.delete("/fichas/{ficha_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ficha(
    ficha_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Desactiva una ficha (soft delete)."""
    ficha = crud.get_ficha(db, ficha_id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")
    crud.soft_delete_ficha(db, ficha)
    return None


# ================== Asignaciones Instructor-Ficha ==================
@router.post(
    "/asignaciones",
    response_model=schemas.AsignacionInstructorFichaOut,
    status_code=status.HTTP_201_CREATED
)
def crear_asignacion(
    asignacion: schemas.AsignacionInstructorFichaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Asigna una ficha a un instructor. Si ya existía una asignación inactiva, la reactiva."""
    ficha = crud.get_ficha(db, asignacion.ficha_id)
    if not ficha or not ficha.is_active:
        raise HTTPException(status_code=404, detail="Ficha no encontrada o inactiva")

    instructor = db.query(Usuario).filter(
        Usuario.id == asignacion.instructor_id,
        Usuario.rol_id == Roles.INSTRUCTOR,
        Usuario.is_active == True
    ).first()
    if not instructor:
        raise HTTPException(status_code=400, detail="El usuario no es un instructor activo")

    # Buscar cualquier asignación previa (activa o inactiva)
    existente = crud.get_asignacion_por_ficha_instructor(
        db, asignacion.ficha_id, asignacion.instructor_id
    )
    if existente:
        if existente.is_active and existente.estado_asignacion == EstadoAsignacion.ACTIVA:
            raise HTTPException(status_code=400, detail="La ficha ya está asignada a este instructor")
        # Si la asignación está inactiva, reactivarla
        return crud.reactivar_asignacion(db, existente)

    data = asignacion.model_dump()
    data["estado_asignacion"] = EstadoAsignacion.ACTIVA
    data["is_active"] = True
    return crud.create_asignacion(db, data)


@router.post(
    "/asignaciones",
    response_model=schemas.AsignacionInstructorFichaOut,
    status_code=status.HTTP_201_CREATED
)
def crear_asignacion(
    asignacion: schemas.AsignacionInstructorFichaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Asigna una ficha a un instructor. Si ya existía una asignación inactiva, la reactiva."""
    ficha = crud.get_ficha(db, asignacion.ficha_id)
    if not ficha or not ficha.is_active:
        raise HTTPException(status_code=404, detail="Ficha no encontrada o inactiva")

    instructor = db.query(Usuario).filter(
        Usuario.id == asignacion.instructor_id,
        Usuario.rol_id == Roles.INSTRUCTOR,
        Usuario.is_active == True
    ).first()
    if not instructor:
        raise HTTPException(status_code=400, detail="El usuario no es un instructor activo")

    # Buscar cualquier asignación previa (activa o inactiva)
    existente = crud.get_asignacion_por_ficha_instructor(
        db, asignacion.ficha_id, asignacion.instructor_id
    )
    if existente:
        if existente.is_active and existente.estado_asignacion == EstadoAsignacion.ACTIVA:
            raise HTTPException(status_code=400, detail="La ficha ya está asignada a este instructor")
        # Si la asignación está inactiva, reactivarla
        return crud.reactivar_asignacion(db, existente)

    data = asignacion.model_dump()
    data["estado_asignacion"] = EstadoAsignacion.ACTIVA
    data["is_active"] = True
    return crud.create_asignacion(db, data)


@router.get("/asignaciones/{asignacion_id}", response_model=schemas.AsignacionInstructorFichaOut)
def obtener_asignacion(
    asignacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una asignación por su ID."""
    asignacion = crud.get_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    # Un instructor solo puede ver su propia asignación
    if current_user.rol_id == Roles.INSTRUCTOR and asignacion.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta asignación")

    return asignacion


@router.patch(
    "/asignaciones/{asignacion_id}",
    response_model=schemas.AsignacionInstructorFichaOut
)
def actualizar_asignacion(
    asignacion_id: int,
    datos: schemas.AsignacionInstructorFichaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Actualiza el estado de una asignación (ACTIVA/INACTIVA)."""
    asignacion = crud.get_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_asignacion(db, asignacion, update_data)


@router.delete("/asignaciones/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(
    asignacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Desactiva una asignación (soft delete)."""
    asignacion = crud.get_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    crud.soft_delete_asignacion(db, asignacion)
    return None