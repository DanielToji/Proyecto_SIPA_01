from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.constants import Roles, RolesPermisos
from app.models import Usuario, Ficha, Charla, AsistenciaCharla
from app.modules.charlas import crud, schemas

router = APIRouter(prefix="/charlas", tags=["charlas"])


# ================== Endpoints de Charla ==================
@router.post("", response_model=schemas.CharlaOut, status_code=status.HTTP_201_CREATED)
def crear_charla(
    charla: schemas.CharlaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """
    Crea una charla de sensibilización (inicial o pre-productiva).
    RF-05: Registrar fechas de selección de alternativa e inducción.
    """
    ficha = db.query(Ficha).filter(Ficha.id == charla.ficha_id, Ficha.is_active == True).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha no encontrada o inactiva")

    instructor = db.query(Usuario).filter(
        Usuario.id == charla.instructor_id,
        Usuario.rol_id == Roles.INSTRUCTOR,
        Usuario.is_active == True
    ).first()
    if not instructor:
        raise HTTPException(status_code=400, detail="El usuario no es un instructor activo")

    data = charla.model_dump()
    data["created_by"] = current_user.id

    return crud.create_charla(db, data)


@router.get("", response_model=list[schemas.CharlaOut])
def listar_charlas(
    ficha_id: Optional[int] = None,
    tipo_charla: Optional[str] = None,
    instructor_id: Optional[int] = None,
    solo_activas: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista charlas con filtros."""
    return crud.list_charlas(
        db,
        ficha_id=ficha_id,
        tipo_charla=tipo_charla,
        instructor_id=instructor_id,
        solo_activas=solo_activas,
        skip=skip,
        limit=limit,
    )


@router.get("/{charla_id}", response_model=schemas.CharlaOut)
def obtener_charla(
    charla_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una charla por ID."""
    charla = crud.get_charla(db, charla_id)
    if not charla:
        raise HTTPException(status_code=404, detail="Charla no encontrada")
    return charla


@router.put("/{charla_id}", response_model=schemas.CharlaOut)
def actualizar_charla(
    charla_id: int,
    datos: schemas.CharlaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Actualiza una charla existente."""
    charla = crud.get_charla(db, charla_id)
    if not charla:
        raise HTTPException(status_code=404, detail="Charla no encontrada")

    if datos.ficha_id:
        ficha = db.query(Ficha).filter(Ficha.id == datos.ficha_id, Ficha.is_active == True).first()
        if not ficha:
            raise HTTPException(status_code=404, detail="Ficha no encontrada o inactiva")

    if datos.instructor_id:
        instructor = db.query(Usuario).filter(
            Usuario.id == datos.instructor_id,
            Usuario.rol_id == Roles.INSTRUCTOR,
            Usuario.is_active == True
        ).first()
        if not instructor:
            raise HTTPException(status_code=400, detail="El usuario no es un instructor activo")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_charla(db, charla, update_data)


@router.delete("/{charla_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_charla(
    charla_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """Desactiva una charla (soft delete)."""
    charla = crud.get_charla(db, charla_id)
    if not charla:
        raise HTTPException(status_code=404, detail="Charla no encontrada")
    crud.soft_delete_charla(db, charla)
    return None


# ================== Endpoints de Asistencia ==================
@router.post(
    "/{charla_id}/asistencias",
    response_model=list[schemas.AsistenciaCharlaOut],
    status_code=status.HTTP_201_CREATED
)
def registrar_asistencias(
    charla_id: int,
    asistencias_data: schemas.AsistenciaCharlaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra o actualiza asistencias de aprendices a una charla.
    - Admin/Coordinador/Apoyo Administrativo pueden registrar.
    - Instructor solo si es el asignado a la charla.
    """
    charla = crud.get_charla(db, charla_id)
    if not charla:
        raise HTTPException(status_code=404, detail="Charla no encontrada")

    # Verificar permisos según rol
    if current_user.rol_id == Roles.INSTRUCTOR:
        if charla.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="No es el instructor asignado a esta charla")
    elif current_user.rol_id not in RolesPermisos.ESCRITURA:
        raise HTTPException(status_code=403, detail="No autorizado para registrar asistencias")

    resultados = []
    for item in asistencias_data.asistencias:
        aprendiz = db.query(Usuario).filter(
            Usuario.id == item.aprendiz_id,
            Usuario.rol_id == Roles.APRENDIZ,
            Usuario.is_active == True
        ).first()
        if not aprendiz:
            raise HTTPException(status_code=400, detail=f"Aprendiz ID {item.aprendiz_id} no válido")

        if not item.asistio and item.fecha_asistencia:
            raise HTTPException(status_code=400, detail="No se puede registrar fecha si no asistió")

        if item.asistio and not item.fecha_asistencia:
            raise HTTPException(status_code=400, detail="Debe indicar fecha de asistencia")

        if item.fecha_asistencia and item.fecha_asistencia < charla.fecha_programada.date():
            raise HTTPException(
                status_code=400,
                detail="La fecha de asistencia no puede ser anterior a la fecha programada de la charla"
            )

        existente = crud.get_asistencia_by_charla_aprendiz(db, charla_id, item.aprendiz_id)
        if existente:
            data = item.model_dump()
            data["is_active"] = True
            asistencia_actualizada = crud.update_asistencia(db, existente, data)
            resultados.append(asistencia_actualizada)
        else:
            data = item.model_dump()
            data["charla_id"] = charla_id
            data["is_active"] = True
            nueva_asistencia = crud.create_asistencia(db, data)
            resultados.append(nueva_asistencia)

    return resultados


@router.get("/{charla_id}/asistencias", response_model=list[schemas.AsistenciaCharlaOut])
def listar_asistencias(
    charla_id: int,
    solo_activas: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista las asistencias de una charla.
    - Aprendiz solo ve su propia asistencia.
    """
    charla = crud.get_charla(db, charla_id)
    if not charla:
        raise HTTPException(status_code=404, detail="Charla no encontrada")

    aprendiz_id = None
    if current_user.rol_id == Roles.APRENDIZ:
        aprendiz_id = current_user.id

    return crud.list_asistencias_charla(
        db,
        charla_id,
        aprendiz_id=aprendiz_id,
        solo_activas=solo_activas,
    )