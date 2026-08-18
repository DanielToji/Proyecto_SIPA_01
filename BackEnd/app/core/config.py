import os
from dataclasses import dataclass, field
from typing import List


def _get_secret_key() -> str:
    """Obtiene SECRET_KEY desde variables de entorno. Obligatoria."""
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY no está definida en las variables de entorno")
    return secret


def _parse_cors_origins(raw: str) -> List[str]:
    """Convierte la variable CORS_ORIGINS en una lista limpia."""
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        return ["http://localhost:5173"]
    return origins


def _parse_bool_env(name: str, default: bool = False) -> bool:
    """Convierte variables booleanas de entorno."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"true", "1", "yes", "on"}


def _parse_int_env(name: str, default: int) -> int:
    """Convierte variables enteras con manejo de errores."""
    raw = os.getenv(name)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    """Configuración central de la aplicación."""

    # Entorno
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    DEBUG: bool = _parse_bool_env("DEBUG", ENVIRONMENT != "production")
    APP_NAME: str = os.getenv("APP_NAME", "SIPA API")

    # Base de datos
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/sipa"
    )
    DEFAULT_SCHEMA: str = os.getenv("DEFAULT_SCHEMA", "etapa_productiva")

    # Seguridad JWT
    SECRET_KEY: str = field(default_factory=_get_secret_key)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _parse_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = _parse_int_env("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 30)

    # CORS
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: _parse_cors_origins(os.getenv("CORS_ORIGINS", "http://localhost:5173"))
    )

    # SMTP genérico
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = _parse_int_env("SMTP_PORT", 1025)
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "sipa@sena.edu.co")
    SMTP_USE_TLS: bool = _parse_bool_env("SMTP_USE_TLS", False)
    SMTP_USE_SSL: bool = _parse_bool_env("SMTP_USE_SSL", False)
    SMTP_TIMEOUT: int = _parse_int_env("SMTP_TIMEOUT", 10)

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Almacenamiento de archivos
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE_MB: int = _parse_int_env("MAX_UPLOAD_SIZE_MB", 5)

    def __post_init__(self):
        """Validaciones posteriores a la carga de variables."""
        self._validar_secret_key()
        self._validar_cors()

    def _validar_secret_key(self):
        """La clave secreta debe tener al menos 32 caracteres."""
        if len(self.SECRET_KEY) < 32:
            raise RuntimeError("SECRET_KEY debe tener al menos 32 caracteres")

    def _validar_cors(self):
        """En producción no se permite '*'. En desarrollo se permite con advertencia."""
        if "*" in self.CORS_ORIGINS and self.ENVIRONMENT == "production":
            raise RuntimeError("CORS_ORIGINS no puede contener '*' en producción")


settings = Settings()