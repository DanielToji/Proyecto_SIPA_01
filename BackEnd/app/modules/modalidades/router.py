from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import RolesPermisos
from app.models import Usuario
from app.modules.modalidades import crud, schemas

router = APIRouter(prefix="/modalidades", tags=["modalidades"])


@router.post("", response_model=schemas.ModalidadEPOut, status_code=status.HTTP_201_CREATED)
def crear_modalidad(
    modalidad: schemas.ModalidadEPCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RolesPermisos.ADMIN, RolesPermisos.COORDINADOR))
):
    """
    Crea una nueva modalidad de etapa productiva.
    Solo administradores y coordinadores pueden crearla.
    """
    if crud.get_modalidad_by_nombre(db, modalidad.nombre):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una modalidad con ese nombre"
        )
    nueva_modalidad = crud.create_modalidad(db, modalidad.model_dump())
    return nueva_modalidad


@router.get("", response_model=list[schemas.ModalidadEPOut])
def listar_modalidades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    solo_activas: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista modalidades con paginación y búsqueda por nombre.
    Cualquier usuario autenticado puede consultar.
    """
    return crud.list_modalidades(db, skip=skip, limit=limit, solo_activas=solo_activas, search=search)


@router.get("/{modalidad_id}", response_model=schemas.ModalidadEPOut)
def obtener_modalidad(
    modalidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una modalidad por su ID.
    """
    modalidad = crud.get_modalidad(db, modalidad_id)
    if not modalidad:
        raise HTTPException(status_code=404, detail="Modalidad no encontrada")
    return modalidad


@router.put("/{modalidad_id}", response_model=schemas.ModalidadEPOut)
def actualizar_modalidad(
    modalidad_id: int,
    datos: schemas.ModalidadEPUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RolesPermisos.ADMIN, RolesPermisos.COORDINADOR))
):
    """
    Actualiza una modalidad existente.
    Solo administradores y coordinadores pueden modificarla.
    """
    modalidad = crud.get_modalidad(db, modalidad_id)
    if not modalidad:
        raise HTTPException(status_code=404, detail="Modalidad no encontrada")

    # Validar unicidad de nombre si se cambia
    if datos.nombre and datos.nombre != modalidad.nombre:
        if crud.get_modalidad_by_nombre(db, datos.nombre):
            raise HTTPException(
                status_code=400,
                detail="Ya existe una modalidad con ese nombre"
            )

    update_data = datos.model_dump(exclude_unset=True)
    modalidad_actualizada = crud.update_modalidad(db, modalidad, update_data)
    return modalidad_actualizada


@router.delete("/{modalidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_modalidad(
    modalidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Desactiva una modalidad (soft delete). No permite desactivar si tiene procesos activos."""
    modalidad = crud.get_modalidad(db, modalidad_id)
    if not modalidad:
        raise HTTPException(status_code=404, detail="Modalidad no encontrada")

    if crud.modalidad_tiene_procesos_activos(db, modalidad_id):
        raise HTTPException(
            status_code=400,
            detail="No se puede desactivar la modalidad porque tiene procesos activos asociados"
        )

    crud.soft_delete_modalidad(db, modalidad)
    return None