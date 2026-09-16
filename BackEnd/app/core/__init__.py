"""
Core del sistema - Configuración, base de datos, seguridad y constantes
"""

from app.core.config import settings
from app.core.database import (
    Base,
    get_db,
    engine,
    SessionLocal,
    set_current_user_id,
    get_current_user_id,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_current_user,
    require_role,
    require_admin,
    require_coordinador,
    require_instructor,
    require_aprendiz,
    require_admin_o_coordinador,
    require_personal_seguimiento,
    oauth2_scheme,
)
from app.core.constants import Roles, RolesPermisos

__all__ = [
    # Configuración
    "settings",
    
    # Base de datos
    "Base",
    "get_db",
    "engine",
    "SessionLocal",
    "set_current_user_id",
    "get_current_user_id",
    
    # Seguridad
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "require_role",
    "require_admin",
    "require_coordinador",
    "require_instructor",
    "require_aprendiz",
    "require_admin_o_coordinador",
    "require_personal_seguimiento",
    "oauth2_scheme",
    
    # Constantes
    "Roles",
    "RolesPermisos",
]