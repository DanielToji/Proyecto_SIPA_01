from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import Roles, RolesPermisos
from app.models import Usuario, EstadoEnvioEmail
from app.modules.notificaciones import crud, schemas, services

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.get("/mis-notificaciones", response_model=list[schemas.NotificacionOut])
def listar_mis_notificaciones(
    estado_envio: Optional[EstadoEnvioEmail] = None,
    solo_activas: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las notificaciones del usuario autenticado."""
    return crud.list_notificaciones_usuario(
        db,
        usuario_id=current_user.id,
        solo_activas=solo_activas,
        estado_envio=estado_envio,
        skip=skip,
        limit=limit,
    )


@router.get("/usuario/{usuario_id}", response_model=list[schemas.NotificacionOut])
def listar_notificaciones_por_usuario(
    usuario_id: int,
    estado_envio: Optional[EstadoEnvioEmail] = None,
    solo_activas: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista notificaciones de un usuario. Solo admin puede ver las de otros."""
    if current_user.rol_id != Roles.ADMIN and current_user.id != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado para ver estas notificaciones")
    return crud.list_notificaciones_usuario(
        db,
        usuario_id=usuario_id,
        solo_activas=solo_activas,
        estado_envio=estado_envio,
        skip=skip,
        limit=limit,
    )


@router.post("/enviar", response_model=schemas.NotificacionOut, status_code=status.HTTP_201_CREATED)
def crear_notificacion_manual(
    notificacion: schemas.NotificacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Crea una notificación manual. Solo admin, coordinador y apoyo administrativo."""
    destinatario = db.query(Usuario).filter(
        Usuario.id == notificacion.destinatario_usuario_id,
        Usuario.is_active == True
    ).first()
    if not destinatario:
        raise HTTPException(status_code=400, detail="El destinatario no existe o está inactivo")

    data = notificacion.model_dump()
    data["remitente_usuario_id"] = current_user.id
    data["estado_envio_email"] = EstadoEnvioEmail.PENDIENTE
    data["is_active"] = True

    return crud.create_notificacion(db, data)


@router.post("/generar-alertas", response_model=schemas.AlertasResult)
def generar_alertas_automaticas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """
    Ejecuta todas las reglas de alerta automática (RF-09).
    Retorna las notificaciones creadas.
    """
    alertas = services.generar_todas_las_alertas(db)
    return {
        "total_alertas_creadas": len(alertas),
        "alertas": alertas,
    }


@router.get("/{notificacion_id}", response_model=schemas.NotificacionOut)
def obtener_notificacion(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una notificación por ID. Solo destinatario o admin."""
    notificacion = crud.get_notificacion(db, notificacion_id)
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if current_user.rol_id != Roles.ADMIN and current_user.id != notificacion.destinatario_usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta notificación")
    return notificacion


@router.patch(
    "/{notificacion_id}/marcar-enviada",
    response_model=schemas.NotificacionOut
)
def marcar_como_enviada(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """
    Marca una notificación como enviada por email.
    Solo admin y coordinador.
    """
    notificacion = crud.get_notificacion(db, notificacion_id)
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return crud.marcar_notificacion_enviada(db, notificacion)


@router.delete("/{notificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_notificacion(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Desactiva una notificación. Solo destinatario o admin."""
    notificacion = crud.get_notificacion(db, notificacion_id)
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if current_user.rol_id != Roles.ADMIN and current_user.id != notificacion.destinatario_usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar esta notificación")
    crud.soft_delete_notificacion(db, notificacion)
    return None