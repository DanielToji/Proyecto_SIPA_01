from typing import Optional, List, Tuple
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models import Usuario, Rol
from app.core.security import get_password_hash


# ============================================================
# FUNCIONES PARA ROLES
# ============================================================

def get_rol(db: Session, rol_id: int) -> Optional[Rol]:
    """Obtiene un rol por su ID"""
    return db.query(Rol).filter(Rol.id == rol_id).first()


def get_rol_by_nombre(db: Session, nombre: str) -> Optional[Rol]:
    """Obtiene un rol por su nombre"""
    return db.query(Rol).filter(Rol.nombre.ilike(nombre.strip())).first()


def list_roles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True,
    search: Optional[str] = None,
) -> List[Rol]:
    """Lista roles con filtros y paginación"""
    query = db.query(Rol)
    if solo_activos:
        query = query.filter(Rol.is_active == True)
    if search:
        query = query.filter(Rol.nombre.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def create_rol(db: Session, data: dict) -> Rol:
    """Crea un nuevo rol"""
    rol = Rol(**data)
    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


def update_rol(db: Session, rol: Rol, data: dict) -> Rol:
    """Actualiza un rol"""
    for key, value in data.items():
        if value is not None:
            setattr(rol, key, value)
    db.commit()
    db.refresh(rol)
    return rol


def soft_delete_rol(db: Session, rol: Rol) -> Rol:
    """Desactiva un rol (soft delete)"""
    rol.is_active = False
    db.commit()
    db.refresh(rol)
    return rol


def get_rol_nombre(db: Session, rol_id: int) -> Optional[str]:
    """Obtiene el nombre de un rol por su ID"""
    rol = get_rol(db, rol_id)
    return rol.nombre if rol else None


# ============================================================
# FUNCIONES PARA USUARIOS
# ============================================================

def get_usuario_by_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Obtiene un usuario por su ID"""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
    """Obtiene un usuario por su email"""
    return db.query(Usuario).filter(Usuario.email == email).first()


def get_usuario_by_documento(db: Session, documento: str) -> Optional[Usuario]:
    """Obtiene un usuario por su documento de identidad"""
    return db.query(Usuario).filter(Usuario.documento_identidad == documento).first()


def get_usuarios(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    rol_id: Optional[int] = None,
    is_active: Optional[bool] = True,
) -> Tuple[List[Usuario], int]:
    """
    Obtiene lista de usuarios con filtros y paginación.
    Retorna (lista_usuarios, total)
    """
    query = db.query(Usuario)
    
    if is_active is not None:
        query = query.filter(Usuario.is_active == is_active)
    
    if rol_id:
        query = query.filter(Usuario.rol_id == rol_id)
    
    if search:
        search_filter = or_(
            Usuario.nombre.ilike(f"%{search}%"),
            Usuario.apellido.ilike(f"%{search}%"),
            Usuario.email.ilike(f"%{search}%"),
            Usuario.documento_identidad.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)
    
    total = query.count()
    usuarios = query.offset(skip).limit(limit).all()
    
    return usuarios, total


def create_usuario(db: Session, usuario_data: dict) -> Usuario:
    """
    Crea un nuevo usuario.
    El diccionario debe contener 'password' que será hasheado.
    """
    password = usuario_data.pop("password", None)
    hashed_password = get_password_hash(password) if password else None
    
    usuario = Usuario(
        **usuario_data,
        password_hash=hashed_password
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def update_usuario(db: Session, usuario: Usuario, update_data: dict) -> Usuario:
    """Actualiza un usuario"""
    # Si se actualiza la contraseña, hashearla
    if "password" in update_data:
        password = update_data.pop("password")
        update_data["password_hash"] = get_password_hash(password)
    
    for key, value in update_data.items():
        if value is not None:
            setattr(usuario, key, value)
    
    db.commit()
    db.refresh(usuario)
    return usuario


def delete_usuario(db: Session, usuario: Usuario) -> Usuario:
    """Desactiva un usuario (soft delete)"""
    usuario.is_active = False
    db.commit()
    db.refresh(usuario)
    return usuario


def activate_usuario(db: Session, usuario: Usuario) -> Usuario:
    """Activa un usuario"""
    usuario.is_active = True
    db.commit()
    db.refresh(usuario)
    return usuario


def contar_administradores_activos(db: Session) -> int:
    """Cuenta cuántos administradores activos hay"""
    return db.query(func.count(Usuario.id)).filter(
        Usuario.rol_id == 1,
        Usuario.is_active == True
    ).scalar()