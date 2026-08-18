from typing import Optional

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models import Usuario, Rol


# ================== Roles ==================
def get_rol(db: Session, rol_id: int) -> Optional[Rol]:
    return db.query(Rol).filter(Rol.id == rol_id).first()


def get_rol_by_nombre(db: Session, nombre: str) -> Optional[Rol]:
    return db.query(Rol).filter(Rol.nombre.ilike(nombre.strip())).first()


def list_roles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True,
    search: Optional[str] = None,
) -> list[Rol]:
    query = db.query(Rol)
    if solo_activos:
        query = query.filter(Rol.is_active == True)
    if search:
        query = query.filter(Rol.nombre.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def create_rol(db: Session, data: dict) -> Rol:
    rol = Rol(**data)
    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


def update_rol(db: Session, rol: Rol, data: dict) -> Rol:
    for key, value in data.items():
        setattr(rol, key, value)
    db.commit()
    db.refresh(rol)
    return rol


def soft_delete_rol(db: Session, rol: Rol) -> Rol:
    rol.is_active = False
    db.commit()
    db.refresh(rol)
    return rol


# ================== Usuarios ==================
def get_usuario(db: Session, usuario_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email == email).first()


def get_usuario_by_documento(db: Session, documento: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.documento_identidad == documento).first()


def list_usuarios(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True,
    rol_id: Optional[int] = None,
    search: Optional[str] = None,
) -> list[Usuario]:
    query = db.query(Usuario)
    if solo_activos:
        query = query.filter(Usuario.is_active == True)
    if rol_id:
        query = query.filter(Usuario.rol_id == rol_id)
    if search:
        query = query.filter(
            or_(
                Usuario.nombre.ilike(f"%{search}%"),
                Usuario.apellido.ilike(f"%{search}%"),
                Usuario.email.ilike(f"%{search}%"),
                Usuario.documento_identidad.ilike(f"%{search}%"),
            )
        )
    return query.offset(skip).limit(limit).all()


def create_usuario(db: Session, data: dict) -> Usuario:
    usuario = Usuario(**data)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def update_usuario(db: Session, usuario: Usuario, data: dict) -> Usuario:
    for key, value in data.items():
        setattr(usuario, key, value)
    db.commit()
    db.refresh(usuario)
    return usuario


def soft_delete_usuario(db: Session, usuario: Usuario) -> Usuario:
    usuario.is_active = False
    db.commit()
    db.refresh(usuario)
    return usuario


def reactivar_usuario(db: Session, usuario: Usuario) -> Usuario:
    usuario.is_active = True
    db.commit()
    db.refresh(usuario)
    return usuario


def contar_administradores_activos(db: Session) -> int:
    return db.query(func.count(Usuario.id)).filter(
        Usuario.rol_id == 1,
        Usuario.is_active == True
    ).scalar()