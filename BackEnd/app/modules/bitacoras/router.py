from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import Roles, RolesPermisos
from app.models import (
    Usuario,
    ProcesoEtapaProductiva,
    EstadoBitacora,
    EstadoProceso,
    EvidenciaArchivo,
)
from app.modules.bitacoras import crud, schemas, services

router = APIRouter(prefix="/bitacoras", tags=["bitacoras"])


@router.post("", response_model=schemas.BitacoraOut, status_code=status.HTTP_201_CREATED)
def subir_bitacora(
    bitacora: schemas.BitacoraCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.APRENDIZ))
):
    """
    Registra una bitácora de etapa productiva asociada al proceso activo del aprendiz.
    RF: Gestión de bitácoras F147.
    """
    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == bitacora.proceso_id,
        ProcesoEtapaProductiva.aprendiz_id == current_user.id,
        ProcesoEtapaProductiva.estado == EstadoProceso.ACTIVO,
        ProcesoEtapaProductiva.is_active == True
    ).first()
    if not proceso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proceso activo no encontrado para este aprendiz"
        )

    existente = crud.get_bitacora_by_proceso_numero(
        db, bitacora.proceso_id, bitacora.numero_bitacora
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una bitácora con ese número para el proceso"
        )

    data = bitacora.model_dump()
    data["estado"] = EstadoBitacora.ENVIADA
    data["fecha_envio"] = datetime.utcnow()
    data["is_active"] = True

    return crud.create_bitacora(db, data)


@router.get("", response_model=list[schemas.BitacoraOut])
def listar_bitacoras(
    proceso_id: Optional[int] = None,
    ficha_id: Optional[int] = None,
    estado_bitacora: Optional[EstadoBitacora] = None,
    estado_proceso: Optional[EstadoProceso] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista bitácoras con filtros y control de acceso:
    - Admin/Coordinador: todas.
    - Instructor: solo de sus procesos asignados.
    - Aprendiz: solo las suyas.
    """
    proceso_ids: Optional[List[int]] = None

    if current_user.rol_id == Roles.APRENDIZ:
        procesos = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.aprendiz_id == current_user.id,
            ProcesoEtapaProductiva.is_active == True
        ).all()
        if not procesos:
            return []
        proceso_ids = [p.id for p in procesos]
    elif current_user.rol_id == Roles.INSTRUCTOR:
        procesos = db.query(ProcesoEtapaProductiva).filter(
            ProcesoEtapaProductiva.instructor_id == current_user.id,
            ProcesoEtapaProductiva.is_active == True
        ).all()
        if not procesos:
            return []
        proceso_ids = [p.id for p in procesos]

    if proceso_id and proceso_ids is not None and proceso_id not in proceso_ids:
        raise HTTPException(status_code=403, detail="No autorizado para ver ese proceso")

    return crud.list_bitacoras(
        db,
        proceso_id=proceso_id,
        proceso_ids=proceso_ids,
        ficha_id=ficha_id,
        estado_bitacora=estado_bitacora,
        estado_proceso=estado_proceso,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit,
    )


@router.get("/{bitacora_id}", response_model=schemas.BitacoraOut)
def obtener_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una bitácora por ID con control de acceso."""
    bitacora = crud.get_bitacora(db, bitacora_id)
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == bitacora.proceso_id
    ).first()
    if current_user.rol_id == Roles.APRENDIZ and proceso.aprendiz_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta bitácora")
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta bitácora")

    return bitacora


@router.put("/{bitacora_id}", response_model=schemas.BitacoraOut)
def actualizar_bitacora(
    bitacora_id: int,
    datos: schemas.BitacoraUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza una bitácora existente.
    Solo el aprendiz dueño puede editarla mientras no esté aprobada.
    """
    bitacora = crud.get_bitacora(db, bitacora_id)
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == bitacora.proceso_id
    ).first()
    if current_user.rol_id == Roles.APRENDIZ and proceso.aprendiz_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para editar esta bitácora")

    if bitacora.estado in [EstadoBitacora.APROBADA, EstadoBitacora.CON_OBSERVACIONES]:
        raise HTTPException(status_code=400, detail="No se puede editar una bitácora ya evaluada")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_bitacora(db, bitacora, update_data)


@router.patch("/{bitacora_id}/evaluar", response_model=schemas.BitacoraOut)
def evaluar_bitacora(
    bitacora_id: int,
    evaluacion: schemas.BitacoraEvaluacion,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.INSTRUCTOR))
):
    """
    Permite al instructor aprobar, rechazar o dejar observaciones en una bitácora.
    """
    bitacora = crud.get_bitacora(db, bitacora_id)
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == bitacora.proceso_id
    ).first()
    if proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")

    return crud.evaluar_bitacora(
        db,
        bitacora,
        evaluacion.estado,
        evaluacion.retroalimentacion
    )


@router.post(
    "/{bitacora_id}/evidencias",
    response_model=schemas.BitacoraEvidenciaOut,
    status_code=status.HTTP_201_CREATED
)
def adjuntar_evidencia(
    bitacora_id: int,
    datos: schemas.BitacoraEvidenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Asocia un archivo de evidencia existente a una bitácora.
    """
    bitacora = crud.get_bitacora(db, bitacora_id)
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == bitacora.proceso_id
    ).first()

    if current_user.rol_id == Roles.APRENDIZ:
        if proceso.aprendiz_id != current_user.id:
            raise HTTPException(status_code=403, detail="No autorizado para adjuntar evidencia")
    elif current_user.rol_id == Roles.INSTRUCTOR:
        if proceso.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="No autorizado para adjuntar evidencia")
    elif current_user.rol_id not in RolesPermisos.ESCRITURA:
        raise HTTPException(status_code=403, detail="No autorizado para adjuntar evidencia")

    evidencia = db.query(EvidenciaArchivo).filter(
        EvidenciaArchivo.id == datos.evidencia_archivo_id,
        EvidenciaArchivo.is_active == True
    ).first()
    if not evidencia:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    return crud.add_evidencia(db, bitacora_id, datos.evidencia_archivo_id)


@router.post(
    "/{bitacora_id}/evidencias/upload",
    response_model=schemas.BitacoraEvidenciaOut,
    status_code=status.HTTP_201_CREATED
)
async def subir_evidencia_bitacora(
    bitacora_id: int,
    file: UploadFile = File(...),
    tipo_documento: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sube un archivo físico de evidencia y lo asocia a la bitácora.
    RF-08: Gestión documental.
    """
    bitacora = crud.get_bitacora(db, bitacora_id)
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    proceso = db.query(ProcesoEtapaProductiva).filter(
        ProcesoEtapaProductiva.id == bitacora.proceso_id
    ).first()

    if current_user.rol_id == Roles.APRENDIZ and proceso.aprendiz_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para subir evidencia")
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para subir evidencia")
    if current_user.rol_id not in RolesPermisos.ESCRITURA and current_user.rol_id not in (Roles.APRENDIZ, Roles.INSTRUCTOR):
        raise HTTPException(status_code=403, detail="No autorizado para subir evidencia")

    evidencia = await services.guardar_evidencia_archivo(
        db,
        file,
        uploaded_by=current_user.id,
        tipo_documento=tipo_documento,
    )

    return crud.add_evidencia(db, bitacora_id, evidencia.id)


@router.get("/{bitacora_id}/evidencias", response_model=list[schemas.BitacoraEvidenciaOut])
def listar_evidencias_bitacora(
    bitacora_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las evidencias asociadas a una bitácora."""
    bitacora = crud.get_bitacora(db, bitacora_id)
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    return crud.list_evidencias(db, bitacora_id)