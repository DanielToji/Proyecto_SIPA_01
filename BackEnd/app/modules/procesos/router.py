from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import Roles
from app.models import (
    Usuario,
    Ficha,
    ModalidadEP,
    Empresa,
    CoordinadorEmpresa,
    ProcesoEtapaProductiva,
    EstadoProceso,
    EstadoSofia,
    TipoNovedad,
)
from app.modules.procesos import crud, schemas

router = APIRouter(prefix="/procesos", tags=["procesos", "checklist"])


# ================== Endpoints de Proceso ==================
@router.post("", response_model=schemas.ProcesoOut, status_code=status.HTTP_201_CREATED)
def crear_proceso(
    proceso: schemas.ProcesoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """
    Crea un proceso de etapa productiva.
    Solo administradores y coordinadores pueden crearlo.
    """
    # Validar aprendiz (debe existir y ser rol aprendiz)
    aprendiz = db.query(Usuario).filter(
        Usuario.id == proceso.aprendiz_id,
        Usuario.rol_id == Roles.APRENDIZ,
        Usuario.is_active == True
    ).first()
    if not aprendiz:
        raise HTTPException(status_code=400, detail="El aprendiz no es válido o no existe")

    # Validar ficha
    ficha = db.query(Ficha).filter(Ficha.id == proceso.ficha_id, Ficha.is_active == True).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")

    # Validar modalidad
    modalidad = db.query(ModalidadEP).filter(
        ModalidadEP.id == proceso.modalidad_id,
        ModalidadEP.is_active == True
    ).first()
    if not modalidad:
        raise HTTPException(status_code=404, detail="Modalidad no encontrada")

    # Validar instructor (debe existir y ser rol instructor)
    instructor = db.query(Usuario).filter(
        Usuario.id == proceso.instructor_id,
        Usuario.rol_id == Roles.INSTRUCTOR,
        Usuario.is_active == True
    ).first()
    if not instructor:
        raise HTTPException(status_code=400, detail="El instructor no es válido o no existe")

    # Validar empresa y coordinador (ambos nulos o ambos no nulos)
    if (proceso.empresa_id is None) != (proceso.coordinador_empresa_id is None):
        raise HTTPException(
            status_code=400,
            detail="Debe indicar empresa y coordinador de empresa juntos o ninguno"
        )

    if proceso.empresa_id is not None:
        empresa = db.query(Empresa).filter(
            Empresa.id == proceso.empresa_id,
            Empresa.is_active == True
        ).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")

        coordinador = db.query(CoordinadorEmpresa).filter(
            CoordinadorEmpresa.id == proceso.coordinador_empresa_id,
            CoordinadorEmpresa.empresa_id == proceso.empresa_id,
            CoordinadorEmpresa.is_active == True
        ).first()
        if not coordinador:
            raise HTTPException(
                status_code=404,
                detail="Coordinador de empresa no encontrado o no pertenece a la empresa"
            )

    data = proceso.model_dump()
    data["estado"] = EstadoProceso.ACTIVO
    data["estado_sofia"] = EstadoSofia.PENDIENTE
    data["is_active"] = True

    nuevo_proceso = crud.create_proceso(db, data)
    return nuevo_proceso


@router.get("", response_model=list[schemas.ProcesoOut])
def listar_procesos(
    aprendiz_id: Optional[int] = None,
    ficha_id: Optional[int] = None,
    modalidad_id: Optional[int] = None,
    empresa_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    estado: Optional[EstadoProceso] = None,
    estado_sofia: Optional[EstadoSofia] = None,
    fecha_inicio_desde: Optional[date] = None,
    fecha_inicio_hasta: Optional[date] = None,
    fecha_fin_desde: Optional[date] = None,
    fecha_fin_hasta: Optional[date] = None,
    solo_activos: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista procesos con filtros. Instructor solo ve sus asignados; aprendiz solo los suyos."""
    if current_user.rol_id == Roles.INSTRUCTOR:
        instructor_id = current_user.id
    elif current_user.rol_id == Roles.APRENDIZ:
        aprendiz_id = current_user.id

    return crud.list_procesos(
        db,
        aprendiz_id=aprendiz_id,
        ficha_id=ficha_id,
        modalidad_id=modalidad_id,
        empresa_id=empresa_id,
        instructor_id=instructor_id,
        estado=estado,
        estado_sofia=estado_sofia,
        fecha_inicio_desde=fecha_inicio_desde,
        fecha_inicio_hasta=fecha_inicio_hasta,
        fecha_fin_desde=fecha_fin_desde,
        fecha_fin_hasta=fecha_fin_hasta,
        solo_activos=solo_activos,
        skip=skip,
        limit=limit,
    )


@router.get("/{proceso_id}/avance", response_model=schemas.ProcesoAvance)
def obtener_avance_proceso(
    proceso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna el porcentaje de avance del proceso según momentos completados."""
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Control de acceso
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este proceso")
    if current_user.rol_id == Roles.APRENDIZ and proceso.aprendiz_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este proceso")

    return crud.calcular_avance_proceso(db, proceso_id)


@router.put("/{proceso_id}", response_model=schemas.ProcesoOut)
def actualizar_proceso(
    proceso_id: int,
    datos: schemas.ProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un proceso.
    - Admin/Coordinador pueden actualizar cualquier campo.
    - Instructor solo puede actualizar notas y observaciones de sus procesos asignados.
    """
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    if current_user.rol_id == Roles.INSTRUCTOR:
        if proceso.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")
        # Instructor solo puede modificar campos de notas/observaciones
        update_data = {}
        if datos.nota_instructor is not None:
            update_data["nota_instructor"] = datos.nota_instructor
        if datos.observaciones is not None:
            update_data["observaciones"] = datos.observaciones
        if datos.estado is not None:
            update_data["estado"] = datos.estado
        if datos.estado_sofia is not None:
            update_data["estado_sofia"] = datos.estado_sofia
        if not update_data:
            raise HTTPException(status_code=400, detail="No tiene permisos para modificar esos campos")
    else:
        # Admin/Coordinador: validar empresa/coordinador si se cambian
        if datos.empresa_id is not None or datos.coordinador_empresa_id is not None:
            # Si viene uno, debe venir el otro
            nueva_empresa = datos.empresa_id if datos.empresa_id is not None else proceso.empresa_id
            nueva_coord = datos.coordinador_empresa_id if datos.coordinador_empresa_id is not None else proceso.coordinador_empresa_id
            if (nueva_empresa is None) != (nueva_coord is None):
                raise HTTPException(
                    status_code=400,
                    detail="Empresa y coordinador deben indicarse juntos o ninguno"
                )
            if nueva_empresa is not None:
                if not db.query(Empresa).filter(Empresa.id == nueva_empresa, Empresa.is_active == True).first():
                    raise HTTPException(status_code=404, detail="Empresa no encontrada")
                if not db.query(CoordinadorEmpresa).filter(
                    CoordinadorEmpresa.id == nueva_coord,
                    CoordinadorEmpresa.empresa_id == nueva_empresa,
                    CoordinadorEmpresa.is_active == True
                ).first():
                    raise HTTPException(status_code=404, detail="Coordinador no válido para la empresa")

        update_data = datos.model_dump(exclude_unset=True)

    return crud.update_proceso(db, proceso, update_data)


@router.delete("/{proceso_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proceso(
    proceso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Desactiva un proceso (soft delete)."""
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    crud.soft_delete_proceso(db, proceso)
    return None


# ================== Endpoints de Checklist Documental ==================
@router.post(
    "/{proceso_id}/checklist",
    response_model=schemas.ChecklistDocumentoOut,
    status_code=status.HTTP_201_CREATED
)
def crear_item_checklist(
    proceso_id: int,
    item: schemas.ChecklistDocumentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Agrega un documento al checklist de un proceso.
    - Admin/Coordinador pueden agregar cualquier documento.
    - Instructor solo si es el asignado al proceso.
    """
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")

    # Validar que no exista ya el mismo tipo de documento para el proceso
    existente = crud.get_checklist_item_by_tipo(db, proceso_id, item.tipo_documento)
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un checklist para ese tipo de documento")

    data = item.model_dump()
    data["proceso_id"] = proceso_id
    data["is_active"] = True
    return crud.create_checklist_item(db, data)


@router.get(
    "/{proceso_id}/checklist",
    response_model=list[schemas.ChecklistDocumentoOut]
)
def listar_checklist_proceso(
    proceso_id: int,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista el checklist documental de un proceso."""
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Aprendiz solo su propio proceso; instructor solo asignado
    if current_user.rol_id == Roles.APRENDIZ and proceso.aprendiz_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este proceso")
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este proceso")

    return crud.list_checklist_proceso(db, proceso_id, solo_activos=solo_activos)


@router.put(
    "/checklist/{item_id}",
    response_model=schemas.ChecklistDocumentoOut
)
def actualizar_item_checklist(
    item_id: int,
    datos: schemas.ChecklistDocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un item del checklist documental.
    - Admin/Coordinador: acceso total.
    - Instructor: solo si está asignado al proceso.
    """
    item = crud.get_checklist_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de checklist no encontrado")

    proceso = crud.get_proceso(db, item.proceso_id)
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para modificar este checklist")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_checklist_item(db, item, update_data)


@router.delete(
    "/checklist/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_item_checklist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Desactiva un item del checklist (soft delete)."""
    item = crud.get_checklist_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de checklist no encontrado")

    proceso = crud.get_proceso(db, item.proceso_id)
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar este checklist")

    crud.soft_delete_checklist_item(db, item)
    return None

    # ================== Endpoints de Evaluación Final ==================
@router.patch(
    "/{proceso_id}/evaluacion",
    response_model=schemas.EvaluacionFinalOut
)
def evaluacion_final(
    proceso_id: int,
    datos: schemas.EvaluacionFinalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra o actualiza la evaluación final del proceso (notas y estado SOFIA).
    Reglas de acceso:
    - Admin y Coordinador pueden actualizar todas las notas y estados.
    - Instructor solo puede actualizar `nota_instructor`, `estado_sofia`, `estado` y `observaciones`
      de sus procesos asignados. No puede modificar `nota_empresa`.
    """
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Control de acceso según rol
    if current_user.rol_id == Roles.INSTRUCTOR:
        if proceso.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")
        # El instructor no puede modificar nota_empresa
        if datos.nota_empresa is not None:
            raise HTTPException(status_code=403, detail="No tiene permisos para modificar la nota de la empresa")
    elif current_user.rol_id not in [Roles.ADMIN, Roles.COORDINADOR]:
        raise HTTPException(status_code=403, detail="No autorizado para realizar evaluación")

    # Construir datos a actualizar
    update_data = datos.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un campo para actualizar")

    # Validar reglas de negocio: si estado_sofia = APROBADO, las notas deben existir y ser >= 3.0
    if datos.estado_sofia == EstadoSofia.APROBADO:
        # Se usa la nota que se está estableciendo o la existente
        nota_empresa_final = datos.nota_empresa if datos.nota_empresa is not None else proceso.nota_empresa
        nota_instructor_final = datos.nota_instructor if datos.nota_instructor is not None else proceso.nota_instructor
        if nota_empresa_final is None or nota_instructor_final is None:
            raise HTTPException(
                status_code=400,
                detail="Para aprobar en SOFIA se requieren ambas notas (empresa e instructor)"
            )
        if nota_empresa_final < 3.0 or nota_instructor_final < 3.0:
            raise HTTPException(
                status_code=400,
                detail="Las notas deben ser iguales o superiores a 3.0 para aprobar"
            )

    # Si se cambia estado a FINALIZADO, debe haber notas y estado_sofia definido
    # Si se cambia estado a FINALIZADO, se debe garantizar que ambas notas existan
    if datos.estado == EstadoProceso.FINALIZADO:
        nota_empresa_final = datos.nota_empresa if datos.nota_empresa is not None else proceso.nota_empresa
        nota_instructor_final = datos.nota_instructor if datos.nota_instructor is not None else proceso.nota_instructor

        if nota_empresa_final is None or nota_instructor_final is None:
            raise HTTPException(
                status_code=400,
                detail="Para finalizar el proceso se requieren ambas notas (empresa e instructor)"
            )

    proceso_actualizado = crud.update_proceso(db, proceso, update_data)
    return proceso_actualizado


# ================== Endpoints de Novedades ==================
@router.post(
    "/{proceso_id}/novedades",
    response_model=schemas.NovedadProcesoOut,
    status_code=status.HTTP_201_CREATED
)
def crear_novedad(
    proceso_id: int,
    novedad: schemas.NovedadProcesoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra una novedad (renuncia, incapacidad, prórroga, etc.) para un proceso.
    - Admin y Coordinador pueden crear cualquier novedad.
    - Instructor solo para sus procesos asignados.
    """
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")
    elif current_user.rol_id not in [Roles.ADMIN, Roles.COORDINADOR, Roles.INSTRUCTOR]:
        raise HTTPException(status_code=403, detail="No autorizado para crear novedades")

    data = novedad.model_dump()
    data["proceso_id"] = proceso_id
    data["is_active"] = True
    return crud.create_novedad(db, data)


@router.get(
    "/{proceso_id}/novedades",
    response_model=list[schemas.NovedadProcesoOut]
)
def listar_novedades_proceso(
    proceso_id: int,
    tipo_novedad: Optional[TipoNovedad] = None,
    solo_activas: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista novedades de un proceso específico.
    - Admin/Coordinador ven todas.
    - Instructor solo si está asignado al proceso.
    - Aprendiz solo si es su propio proceso.
    """
    proceso = crud.get_proceso(db, proceso_id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Control de acceso
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver estas novedades")
    if current_user.rol_id == Roles.APRENDIZ and proceso.aprendiz_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver estas novedades")

    return crud.list_novedades(
        db,
        proceso_id=proceso_id,
        tipo_novedad=tipo_novedad,
        solo_activas=solo_activas,
    )


@router.get("/novedades/{novedad_id}", response_model=schemas.NovedadProcesoOut)
def obtener_novedad(
    novedad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una novedad por su ID con control de acceso."""
    novedad = crud.get_novedad(db, novedad_id)
    if not novedad:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")

    proceso = crud.get_proceso(db, novedad.proceso_id)
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta novedad")
    if current_user.rol_id == Roles.APRENDIZ and proceso.aprendiz_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta novedad")

    return novedad


@router.put("/novedades/{novedad_id}", response_model=schemas.NovedadProcesoOut)
def actualizar_novedad(
    novedad_id: int,
    datos: schemas.NovedadProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza una novedad.
    - Admin/Coordinador: acceso total.
    - Instructor: solo si está asignado al proceso de la novedad.
    """
    novedad = crud.get_novedad(db, novedad_id)
    if not novedad:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")

    proceso = crud.get_proceso(db, novedad.proceso_id)
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_novedad(db, novedad, update_data)


@router.delete("/novedades/{novedad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_novedad(
    novedad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Desactiva una novedad (soft delete).
    - Admin/Coordinador: acceso total.
    - Instructor: solo si está asignado al proceso.
    """
    novedad = crud.get_novedad(db, novedad_id)
    if not novedad:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")

    proceso = crud.get_proceso(db, novedad.proceso_id)
    if current_user.rol_id == Roles.INSTRUCTOR and proceso.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No es el instructor asignado a este proceso")

    crud.soft_delete_novedad(db, novedad)
    return None