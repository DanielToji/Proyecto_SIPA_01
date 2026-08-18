from typing import Optional
from sqlalchemy.orm import Session

from app.models import Usuario


def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
    """Obtiene un usuario por email (sin filtrar por activo)."""
    return db.query(Usuario).filter(Usuario.email == email).first()


def get_usuario_by_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    """Obtiene un usuario por ID."""
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def update_password(db: Session, usuario: Usuario, new_password_hash: str) -> Usuario:
    """Actualiza el hash de contraseña de un usuario."""
    usuario.password_hash = new_password_hash
    db.commit()
    db.refresh(usuario)
    return usuario