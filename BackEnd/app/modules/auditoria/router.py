from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.core.constants import Roles
from app.models import Usuario
from app.modules.auditoria import crud, schemas

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("", response_model=list[schemas.AuditoriaOut])
def listar_auditoria(
    tabla: Optional[str] = Query(None, description="Filtrar por nombre de tabla"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuario que realizó la acción"),
    accion: Optional[str] = Query(
        None,
        pattern="^(INSERT|UPDATE|DELETE)$",
        description="Tipo de acción registrada"
    ),
    desde: Optional[datetime] = Query(None, description="Fecha inicial"),
    hasta: Optional[datetime] = Query(None, description="Fecha final"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN))
):
    """
    Consulta el historial de auditoría de cambios.
    RF-13: Historial completo de modificaciones por registro.
    Solo accesible para administradores.
    """
    return crud.list_auditoria(
        db,
        tabla=tabla,
        usuario_id=usuario_id,
        accion=accion,
        desde=desde,
        hasta=hasta,
        skip=skip,
        limit=limit,
    )


@router.get("/contar")
def contar_auditoria(
    tabla: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    accion: Optional[str] = Query(None, pattern="^(INSERT|UPDATE|DELETE)$"),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN))
):
    """
    Retorna el total de registros de auditoría que coinciden con los filtros.
    """
    total = crud.count_auditoria(
        db,
        tabla=tabla,
        usuario_id=usuario_id,
        accion=accion,
        desde=desde,
        hasta=hasta,
    )
    return {"total": total}