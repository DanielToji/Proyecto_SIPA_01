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


    

# ============================================================
# CARGA MASIVA DE USUARIOS
# ============================================================
import io
from datetime import datetime

import pandas as pd
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash


def bulk_create_usuarios(db: Session, file_content: bytes, filename: str) -> dict:
    """
    Procesa Excel/CSV con usuarios y crea los válidos.
    Retorna resumen con éxitos y errores por fila.
    """
    # ---- 1. Leer archivo ----
    try:
        if filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_content), encoding="latin-1")
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo: {str(e)}")

    # ---- 2. Normalizar columnas ----
    df.columns = [str(c).strip().lower() for c in df.columns]

    required = ["nombre", "apellido", "email", "password", "rol_id"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {', '.join(missing)}. "
            f"Columnas encontradas: {', '.join(df.columns.tolist())}"
        )

    # ---- 3. Cache de roles válidos ----
    roles_validos = {r.id for r in db.query(Rol.id).all()}

    # ---- 4. Procesar fila por fila ----
    total = len(df)
    exitosos = 0
    fallidos = 0
    errores = []

    for idx, row in df.iterrows():
        fila_num = int(idx) + 2
        try:
            # --- rol_id ---
            rol_id_raw = row.get("rol_id")
            if pd.isna(rol_id_raw):
                raise ValueError("rol_id es requerido")
            try:
                rol_id = int(rol_id_raw)
            except (ValueError, TypeError):
                raise ValueError(f"rol_id inválido: {rol_id_raw}")

            if rol_id not in roles_validos:
                raise ValueError(f"Rol {rol_id} no existe")

            # --- nombre / apellido ---
            nombre = str(row.get("nombre", "")).strip()
            apellido = str(row.get("apellido", "")).strip()
            if not nombre:
                raise ValueError("nombre es requerido")
            if not apellido:
                raise ValueError("apellido es requerido")

            # --- email ---
            email = str(row.get("email", "")).strip().lower()
            if not email or "@" not in email:
                raise ValueError(f"Email inválido: {email}")

            # --- password ---
            password = str(row.get("password", ""))
            if len(password) < 8:
                raise ValueError("La contraseña debe tener al menos 8 caracteres")

            # --- tipo_documento ---
            tipo_doc = None
            tipo_doc_raw = row.get("tipo_documento")
            if pd.notna(tipo_doc_raw) and str(tipo_doc_raw).strip():
                td = str(tipo_doc_raw).strip().upper()
                if td not in {"TI", "CC", "CE", "PTE"}:
                    raise ValueError(f"tipo_documento inválido: {td}")
                tipo_doc = td

            # --- documento_identidad / telefono ---
            documento = None
            doc_raw = row.get("documento_identidad")
            if pd.notna(doc_raw) and str(doc_raw).strip():
                documento = str(doc_raw).strip()

            telefono = None
            tel_raw = row.get("telefono")
            if pd.notna(tel_raw) and str(tel_raw).strip():
                telefono = str(tel_raw).strip()

            # --- Verificar duplicados ---
            if db.query(Usuario).filter(Usuario.email == email).first():
                raise ValueError(f"Email duplicado: {email}")
            if documento and db.query(Usuario).filter(
                Usuario.documento_identidad == documento
            ).first():
                raise ValueError(f"Documento duplicado: {documento}")

            # --- Crear instancia ---
            usuario = Usuario(
                nombre=nombre,
                apellido=apellido,
                email=email,
                password_hash=get_password_hash(password),
                tipo_documento=tipo_doc,
                documento_identidad=documento,
                telefono=telefono,
                rol_id=rol_id,
                is_active=True,
            )

            # --- SAVEPOINT ---
            nested = db.begin_nested()
            try:
                db.add(usuario)
                nested.commit()
                exitosos += 1
            except IntegrityError as e:
                nested.rollback()
                err_msg = str(e.orig) if hasattr(e, "orig") else str(e)
                if "email" in err_msg.lower():
                    err_msg = f"Email duplicado: {email}"
                elif "documento" in err_msg.lower():
                    err_msg = f"Documento duplicado: {documento}"
                raise ValueError(err_msg)

        except ValueError as e:
            fallidos += 1
            errores.append({
                "fila": fila_num,
                "error": str(e),
                "data": {k: str(v) for k, v in row.items() if pd.notna(v)},
            })
        except Exception as e:
            fallidos += 1
            errores.append({
                "fila": fila_num,
                "error": f"Error inesperado: {str(e)}",
                "data": {k: str(v) for k, v in row.items() if pd.notna(v)},
            })

    db.commit()
    return {
        "total": total,
        "exitosos": exitosos,
        "fallidos": fallidos,
        "errores": errores,
    }


def generar_plantilla_excel() -> bytes:
    """
    Genera un archivo Excel plantilla para carga masiva de usuarios.
    """
    df = pd.DataFrame([
        {
            "nombre": "Juan",
            "apellido": "Perez",
            "email": "juan.perez@test.com",
            "password": "Test1234!",
            "rol_id": 4,
            "tipo_documento": "CC",
            "documento_identidad": "1023456789",
            "telefono": "3001234567",
        },
        {
            "nombre": "Maria",
            "apellido": "Gomez",
            "email": "maria.gomez@test.com",
            "password": "Test1234!",
            "rol_id": 3,
            "tipo_documento": "CC",
            "documento_identidad": "1023456790",
            "telefono": "3001234568",
        },
    ])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Usuarios")
    buffer.seek(0)
    return buffer.getvalue()