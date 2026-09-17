from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, require_role
from app.core.constants import Roles
from app.models import Usuario, Rol
from app.modules.usuarios import schemas, crud

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# ============================================================
# ENDPOINTS DE ROLES (solo ADMIN)
# ============================================================

@router.get("/roles", response_model=List[schemas.RolOut])
def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene todos los roles del sistema"""
    roles = crud.list_roles(db, skip=skip, limit=limit, search=search)
    return roles


@router.post("/roles", response_model=schemas.RolOut, status_code=status.HTTP_201_CREATED)
def create_rol(
    data: schemas.RolCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo rol"""
    existing = crud.get_rol_by_nombre(db, data.nombre)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del rol ya existe"
        )
    
    new_rol = crud.create_rol(db, data.model_dump())
    return new_rol


@router.put("/roles/{rol_id}", response_model=schemas.RolOut)
def update_rol(
    rol_id: int,
    data: schemas.RolUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza un rol"""
    rol = crud.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    updated_rol = crud.update_rol(db, rol, update_data)
    return updated_rol


@router.delete("/roles/{rol_id}")
def delete_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Desactiva un rol"""
    rol = crud.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Verificar si hay usuarios con este rol
    usuarios_con_rol = db.query(Usuario).filter(Usuario.rol_id == rol_id).first()
    if usuarios_con_rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede desactivar el rol porque tiene usuarios asociados"
        )
    
    crud.soft_delete_rol(db, rol)
    return {"message": "Rol desactivado exitosamente"}


# ============================================================
# ENDPOINTS DE USUARIOS
# ============================================================

@router.get("/me", response_model=schemas.UsuarioOut)
def get_current_user_info(
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene la información del usuario autenticado"""
    return current_user


@router.get("/", response_model=List[schemas.UsuarioOut])
def get_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    rol_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Obtiene lista de usuarios con filtros y paginación"""
    usuarios, total = crud.get_usuarios(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        rol_id=rol_id,
        is_active=is_active
    )
    return usuarios


@router.get("/{usuario_id}", response_model=schemas.UsuarioOut)
def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(Roles.ADMIN, Roles.COORDINADOR))
):
    """Obtiene un usuario por su ID"""
    usuario = crud.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario


@router.post("/", response_model=schemas.UsuarioOut, status_code=status.HTTP_201_CREATED)
def create_usuario(
    data: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo usuario"""
    # Verificar email único
    existing_email = crud.get_usuario_by_email(db, data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Verificar documento único
    if data.documento_identidad:
        existing_doc = crud.get_usuario_by_documento(db, data.documento_identidad)
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado"
            )
    
    # Crear usuario
    usuario_data = data.model_dump()
    new_usuario = crud.create_usuario(db, usuario_data)
    return new_usuario


@router.put("/{usuario_id}", response_model=schemas.UsuarioOut)
def update_usuario(
    usuario_id: int,
    data: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza un usuario"""
    usuario = crud.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Verificar email único si se actualiza
    if "email" in update_data:
        existing_email = crud.get_usuario_by_email(db, update_data["email"])
        if existing_email and existing_email.id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso"
            )
    
    # Verificar documento único si se actualiza
    if "documento_identidad" in update_data and update_data["documento_identidad"]:
        existing_doc = crud.get_usuario_by_documento(db, update_data["documento_identidad"])
        if existing_doc and existing_doc.id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está en uso"
            )
    
    updated_usuario = crud.update_usuario(db, usuario, update_data)
    return updated_usuario


@router.patch("/{usuario_id}/preferencias")
def update_preferencias(
    usuario_id: int,
    data: schemas.PreferenciasUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza las preferencias de UI del usuario"""
    if usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar las preferencias de otro usuario"
        )
    
    current_user.preferencias_ui = data.preferencias_ui
    db.commit()
    db.refresh(current_user)
    return {"message": "Preferencias actualizadas", "preferencias": current_user.preferencias_ui}


@router.delete("/{usuario_id}")
def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Desactiva un usuario (soft delete)"""
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio usuario"
        )
    
    usuario = crud.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    crud.delete_usuario(db, usuario)
    return {"message": "Usuario desactivado exitosamente"}


@router.post("/{usuario_id}/activate")
def activate_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Activa un usuario"""
    usuario = crud.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    crud.activate_usuario(db, usuario)
    return {"message": "Usuario activado exitosamente"}


# ============================================================
# ESTADÍSTICAS
# ============================================================

@router.get("/stats/total")
def get_usuarios_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene estadísticas de usuarios"""
    total = db.query(Usuario).filter(Usuario.is_active == True).count()
    
    # 🔥 FIX: usar func.count (importado de sqlalchemy)
    por_rol = db.query(
        Usuario.rol_id,
        func.count(Usuario.id)
    ).filter(Usuario.is_active == True).group_by(Usuario.rol_id).all()
    
    roles = {}
    for rol_id, count in por_rol:
        rol = crud.get_rol(db, rol_id)
        roles[rol.nombre if rol else f"Rol {rol_id}"] = count
    
    return {
        "total": total,
        "por_rol": roles,
        "administradores_activos": crud.contar_administradores_activos(db)
    }