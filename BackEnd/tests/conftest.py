import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models import Rol, Usuario

# URL de base de datos de pruebas (PostgreSQL)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/sipa_test"
)

engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crea el esquema y las tablas antes de la sesión de pruebas."""
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS etapa_productiva"))
    Base.metadata.create_all(bind=engine)
    yield
    # Limpieza opcional: descomentar para eliminar el esquema al final
    # with engine.begin() as conn:
    #     conn.execute(text("DROP SCHEMA etapa_productiva CASCADE"))
    # engine.dispose()


@pytest.fixture()
def db_session():
    """Provee una sesión de base de datos para una prueba."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """Cliente de pruebas con override de dependencia de BD."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_roles(db_session):
    """Inserta los roles básicos si no existen."""
    roles = [
        {"id": 1, "nombre": "ADMIN", "descripcion": "Administrador"},
        {"id": 2, "nombre": "COORDINADOR", "descripcion": "Coordinador"},
        {"id": 3, "nombre": "INSTRUCTOR", "descripcion": "Instructor"},
        {"id": 4, "nombre": "APRENDIZ", "descripcion": "Aprendiz"},
        {"id": 5, "nombre": "APOYO_ADMINISTRATIVO", "descripcion": "Apoyo Administrativo"},
        {"id": 6, "nombre": "CONSULTA", "descripcion": "Consulta"},
    ]
    for r in roles:
        if not db_session.query(Rol).filter(Rol.id == r["id"]).first():
            db_session.add(Rol(**r))
    db_session.commit()


@pytest.fixture()
def seed_usuarios(db_session, seed_roles):
    """Crea usuarios de prueba para los roles principales."""
    usuarios = [
        {
            "nombre": "Admin",
            "apellido": "Test",
            "email": "admin@test.com",
            "password_hash": get_password_hash("Admin123!"),
            "rol_id": 1,
            "is_active": True,
        },
        {
            "nombre": "Instructor",
            "apellido": "Test",
            "email": "instructor@test.com",
            "password_hash": get_password_hash("Instructor123!"),
            "rol_id": 3,
            "is_active": True,
        },
        {
            "nombre": "Aprendiz",
            "apellido": "Test",
            "email": "aprendiz@test.com",
            "password_hash": get_password_hash("Aprendiz123!"),
            "rol_id": 4,
            "is_active": True,
        },
    ]
    for u in usuarios:
        if not db_session.query(Usuario).filter(Usuario.email == u["email"]).first():
            db_session.add(Usuario(**u))
    db_session.commit()


@pytest.fixture()
def auth_headers(client, seed_usuarios):
    """Retorna helpers para obtener token de cada rol."""
    def _get_token(email: str, password: str) -> dict:
        response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200, f"Login falló: {response.text}"
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _get_token