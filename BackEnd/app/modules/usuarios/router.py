from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash, require_role
from app.core.constants import Roles, RolesPermisos
from app.models import Usuario
from app.modules.usuarios import crud, schemas

router = APIRouter(tags=["usuarios", "roles"])


# ================== Roles ==================
@router.post("/roles", response_model=schemas.RolOut, status_code=status.HTTP_201_CREATED)
def crear_rol(
    rol: schemas.RolCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SOLO_ADMIN))
):
    """Crea un nuevo rol. Solo administradores."""
    if crud.get_rol_by_nombre(db, rol.nombre):
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
    return crud.create_rol(db, rol.model_dump())


@router.get("/roles", response_model=list[schemas.RolOut])
def listar_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista roles. Disponible para cualquier usuario autenticado."""
    return crud.list_roles(db, skip=skip, limit=limit, solo_activos=solo_activos, search=search)


@router.get("/roles/{rol_id}", response_model=schemas.RolOut)
def obtener_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un rol por ID."""
    rol = crud.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol


@router.put("/roles/{rol_id}", response_model=schemas.RolOut)
def actualizar_rol(
    rol_id: int,
    datos: schemas.RolUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SOLO_ADMIN))
):
    """Actualiza un rol. Solo administradores."""
    rol = crud.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if datos.nombre and datos.nombre != rol.nombre:
        if crud.get_rol_by_nombre(db, datos.nombre):
            raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_rol(db, rol, update_data)


@router.delete("/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.SOLO_ADMIN))
):
    """Desactiva un rol. Solo administradores."""
    rol = crud.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    crud.soft_delete_rol(db, rol)
    return None


# ================== Usuarios ==================
@router.post("/usuarios", response_model=schemas.UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """
    Crea un nuevo usuario (aprendiz, instructor, coordinador, etc.).
    Pueden crear: Admin, Coordinador y Apoyo Administrativo.
    """
    if crud.get_usuario_by_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    if usuario.documento_identidad and crud.get_usuario_by_documento(db, usuario.documento_identidad):
        raise HTTPException(status_code=400, detail="El documento ya está registrado")

    if not crud.get_rol(db, usuario.rol_id):
        raise HTTPException(status_code=400, detail="El rol especificado no existe")

    data = usuario.model_dump(exclude={"password"})
    data["password_hash"] = get_password_hash(usuario.password)
    data["is_active"] = True

    return crud.create_usuario(db, data)


@router.get("/usuarios", response_model=list[schemas.UsuarioOut])
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    rol_id: Optional[int] = None,
    search: Optional[str] = None,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista usuarios con filtros.
    - Admin/Coordinador/Apoyo Administrativo: todos.
    - Instructor: solo aprendices (rol_id=4).
    - Aprendiz: solo su propio perfil (usar /usuarios/{id}).
    - Consulta: solo lectura de todos.
    """
    if current_user.rol_id == Roles.INSTRUCTOR:
        rol_id = Roles.APRENDIZ

    return crud.list_usuarios(
        db, skip=skip, limit=limit, solo_activos=solo_activos,
        rol_id=rol_id, search=search
    )


@router.get("/usuarios/{usuario_id}", response_model=schemas.UsuarioOut)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un usuario por ID.
    - Aprendiz solo puede ver su propio perfil.
    """
    if current_user.rol_id == Roles.APRENDIZ and current_user.id != usuario_id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este usuario")

    usuario = crud.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/usuarios/{usuario_id}", response_model=schemas.UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    datos: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un usuario.
    - Admin: puede actualizar cualquier usuario (incluido rol/is_active).
    - Coordinador/Apoyo: puede actualizar datos básicos de aprendices/instructores.
    - Usuario no admin: solo puede actualizar sus propios datos básicos (sin rol/is_active).
    """
    usuario = crud.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Si no es admin, limitar capacidad
    if current_user.rol_id != Roles.ADMIN:
        # Solo puede actualizar su propio perfil
        if current_user.id != usuario_id:
            raise HTTPException(status_code=403, detail="No autorizado para actualizar este usuario")
        # No puede cambiar rol ni estado activo
        datos.rol_id = None
        datos.is_active = None

    # Validar unicidad de email si se cambia
    if datos.email and datos.email != usuario.email:
        if crud.get_usuario_by_email(db, datos.email):
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # Validar unicidad de documento si se cambia
    if datos.documento_identidad and datos.documento_identidad != usuario.documento_identidad:
        if crud.get_usuario_by_documento(db, datos.documento_identidad):
            raise HTTPException(status_code=400, detail="El documento ya está registrado")

    # Validar rol si se envía
    if datos.rol_id and not crud.get_rol(db, datos.rol_id):
        raise HTTPException(status_code=400, detail="El rol especificado no existe")

    update_data = datos.model_dump(exclude_unset=True)
    return crud.update_usuario(db, usuario, update_data)


@router.patch("/usuarios/{usuario_id}/desactivar", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """
    Desactiva un usuario (soft delete).
    - No se puede desactivar a sí mismo.
    - No se puede desactivar al último administrador activo.
    """
    usuario = crud.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if current_user.id == usuario_id:
        raise HTTPException(status_code=400, detail="No puede desactivarse a sí mismo")

    if usuario.rol_id == Roles.ADMIN and crud.contar_administradores_activos(db) <= 1:
        raise HTTPException(status_code=400, detail="No se puede desactivar al último administrador activo")

    crud.soft_delete_usuario(db, usuario)
    return None


@router.patch("/usuarios/{usuario_id}/activar", response_model=schemas.UsuarioOut)
def activar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*RolesPermisos.ESCRITURA))
):
    """
    Reactiva un usuario previamente desactivado.
    """
    usuario = crud.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if usuario.is_active:
        raise HTTPException(status_code=400, detail="El usuario ya está activo")

    return crud.reactivar_usuario(db, usuario)


@router.put("/usuarios/preferencias", response_model=schemas.UsuarioOut)
def actualizar_preferencias(
    preferencias: schemas.PreferenciasUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza las preferencias de interfaz del usuario autenticado."""
    current_user.preferencias_ui = preferencias.preferencias_ui
    db.commit()
    db.refresh(current_user)
    return current_user