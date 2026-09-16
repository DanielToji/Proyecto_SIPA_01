"""
Módulo de Autenticación
- Login / Register
- JWT Tokens
- Cambio y recuperación de contraseña
"""

from app.modules.auth.router import router
from app.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserInfoResponse,
    RegisterRequest,
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm,
    UsuarioMe,
)
from app.modules.auth.crud import (
    get_usuario_by_email,
    get_usuario_by_id,
    update_password,
)
from app.modules.auth.services import send_password_reset_email

__all__ = [
    "router",
    "LoginRequest",
    "TokenResponse",
    "UserInfoResponse",
    "RegisterRequest",
    "PasswordChange",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "UsuarioMe",
    "get_usuario_by_email",
    "get_usuario_by_id",
    "update_password",
    "send_password_reset_email",
]