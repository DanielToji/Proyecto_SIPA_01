import contextvars
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# ContextVar para almacenar el ID del usuario autenticado durante la peticion.
current_user_id_ctx: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "current_user_id", default=None
)


def set_current_user_id(user_id: Optional[int]) -> None:
    """Establece el ID del usuario autenticado en el contexto actual."""
    current_user_id_ctx.set(user_id)


def get_current_user_id() -> Optional[int]:
    """Obtiene el ID del usuario autenticado desde el contexto actual."""
    return current_user_id_ctx.get()


# Motor de base de datos con pool_pre_ping para manejar reconexiones
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG if hasattr(settings, "DEBUG") else False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


# Clase base declarativa para SQLAlchemy 1.4
Base = declarative_base()


@event.listens_for(SessionLocal, "after_begin")
def set_audit_user_in_session(session, transaction, connection):
    """
    Establece la variable de sesion PostgreSQL `app.current_user_id`
    al inicio de cada transaccion.
    """
    user_id = current_user_id_ctx.get()
    if user_id is not None:
        connection.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user_id)}
        )


def get_db():
    """
    Dependencia que provee una sesion de base de datos por peticion.
    Se cierra automaticamente al finalizar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()