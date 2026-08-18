from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import RolesPermisos, Roles
from app.models import Usuario
from app.modules.empresas import crud, schemas

router = APIRouter(prefix="/empresas", tags=["empresas"])


# ================== Empresa ==================
@router.post("", response_model=schemas.EmpresaOut, status_code=status.HTTP_201_CREATED)
def crear_empresa(
    empresa: schemas.EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Crea una nueva empresa co-formadora."""
    if crud.get_empresa_by_nit(db, empresa.nit):
        raise HTTPException(status_code=400, detail="Ya existe una empresa con ese NIT")
    return crud.create_empresa(db, empresa.model_dump())


@router.get("", response_model=list[schemas.EmpresaOut])
def listar_empresas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    solo_activas: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista empresas con búsqueda y paginación."""
    return crud.list_empresas(db, skip=skip, limit=limit, solo_activas=solo_activas, search=search)


@router.get("/{empresa_id}", response_model=schemas.EmpresaOut)
def obtener_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una empresa por ID."""
    empresa = crud.get_empresa(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa


@router.put("/{empresa_id}", response_model=schemas.EmpresaOut)
def actualizar_empresa(
    empresa_id: int,
    datos: schemas.EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Actualiza una empresa existente."""
    empresa = crud.get_empresa(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if datos.nit and datos.nit != empresa.nit:
        if crud.get_empresa_by_nit(db, datos.nit):
            raise HTTPException(status_code=400, detail="Ya existe una empresa con ese NIT")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_empresa(db, empresa, update_data)


@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """
    Desactiva una empresa (soft delete).
    No permite desactivar si tiene procesos activos asociados.
    """
    empresa = crud.get_empresa(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if crud.empresa_tiene_procesos_activos(db, empresa_id):
        raise HTTPException(
            status_code=400,
            detail="No se puede desactivar la empresa porque tiene procesos activos asociados"
        )

    crud.soft_delete_empresa(db, empresa)
    return None


# ================== Coordinador de Empresa ==================
@router.post(
    "/{empresa_id}/coordinadores",
    response_model=schemas.CoordinadorEmpresaOut,
    status_code=status.HTTP_201_CREATED
)
def crear_coordinador_empresa(
    empresa_id: int,
    coordinador: schemas.CoordinadorEmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Registra un coordinador para una empresa existente."""
    empresa = crud.get_empresa(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if coordinador.empresa_id != empresa_id:
        raise HTTPException(status_code=400, detail="El empresa_id del cuerpo no coincide con la ruta")

    if coordinador.correo and crud.get_coordinador_by_email(db, coordinador.correo):
        raise HTTPException(status_code=400, detail="Ya existe un coordinador con ese correo")

    return crud.create_coordinador_empresa(db, coordinador.model_dump())


@router.get(
    "/{empresa_id}/coordinadores",
    response_model=list[schemas.CoordinadorEmpresaOut]
)
def listar_coordinadores_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los coordinadores de una empresa."""
    empresa = crud.get_empresa(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return crud.list_coordinadores_empresa(db, empresa_id)


@router.get(
    "/coordinadores/{coordinador_id}",
    response_model=schemas.CoordinadorEmpresaOut
)
def obtener_coordinador_empresa(
    coordinador_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un coordinador por ID."""
    coordinador = crud.get_coordinador_empresa(db, coordinador_id)
    if not coordinador:
        raise HTTPException(status_code=404, detail="Coordinador no encontrado")
    return coordinador


@router.put(
    "/coordinadores/{coordinador_id}",
    response_model=schemas.CoordinadorEmpresaOut
)
def actualizar_coordinador_empresa(
    coordinador_id: int,
    datos: schemas.CoordinadorEmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Actualiza un coordinador de empresa."""
    coordinador = crud.get_coordinador_empresa(db, coordinador_id)
    if not coordinador:
        raise HTTPException(status_code=404, detail="Coordinador no encontrado")

    if datos.correo and datos.correo != coordinador.correo:
        if crud.get_coordinador_by_email(db, datos.correo):
            raise HTTPException(status_code=400, detail="Ya existe un coordinador con ese correo")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_coordinador_empresa(db, coordinador, update_data)


@router.delete(
    "/coordinadores/{coordinador_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_coordinador_empresa(
    coordinador_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """
    Desactiva un coordinador (soft delete).
    No permite desactivar si tiene procesos activos asociados.
    """
    coordinador = crud.get_coordinador_empresa(db, coordinador_id)
    if not coordinador:
        raise HTTPException(status_code=404, detail="Coordinador no encontrado")

    if crud.coordinador_tiene_procesos_activos(db, coordinador_id):
        raise HTTPException(
            status_code=400,
            detail="No se puede desactivar el coordinador porque tiene procesos activos asociados"
        )

    crud.soft_delete_coordinador_empresa(db, coordinador)
    return None