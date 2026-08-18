from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.config import settings

# ============================================================
# Enumeraciones de negocio
# ============================================================
class EstadoBitacora(str, PyEnum):
    BORRADOR = "BORRADOR"
    ENVIADA = "ENVIADA"
    APROBADA = "APROBADA"
    CON_OBSERVACIONES = "CON_OBSERVACIONES"


class MomentoReunion(str, PyEnum):
    MOMENTO_1_INICIAL = "MOMENTO_1_INICIAL"
    MOMENTO_2_PARCIAL = "MOMENTO_2_PARCIAL"
    MOMENTO_3_FINAL = "MOMENTO_3_FINAL"


class TipoCharla(str, PyEnum):
    CHARLA_INICIAL = "CHARLA_INICIAL"
    CHARLA_PRE_PRODUCTIVA = "CHARLA_PRE_PRODUCTIVA"


class EstadoProceso(str, PyEnum):
    ACTIVO = "ACTIVO"
    FINALIZADO = "FINALIZADO"
    APLAZADO = "APLAZADO"
    RETIRADO = "RETIRADO"  # reemplaza CANCELADO según schema.sql


class EstadoSofia(str, PyEnum):
    PENDIENTE = "PENDIENTE"
    POR_EVALUAR = "POR_EVALUAR"
    APROBADO = "APROBADO"
    NO_APROBADO = "NO_APROBADO"


class TipoNovedad(str, PyEnum):
    RENUNCIA = "RENUNCIA"
    INCAPACIDAD = "INCAPACIDAD"
    CAMBIO_EMPRESA = "CAMBIO_EMPRESA"
    PRORROGA = "PRORROGA"
    OTRO = "OTRO"


class EstadoEnvioEmail(str, PyEnum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    ERROR = "ERROR"


class EstadoAsignacion(str, PyEnum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"


class TipoDocumento(str, PyEnum):
    TI = "TI"
    CC = "CC"
    CE = "CE"
    PTE = "PTE"


class EstadoDocumento(str, PyEnum):
    ENTREGADO = "ENTREGADO"
    PENDIENTE = "PENDIENTE"
    NO_APLICA = "NO_APLICA"


class EstadoMedidaFormativa(str, PyEnum):
    SI = "SI"
    NO = "NO"
    PENDIENTE = "PENDIENTE"


class EstadoCorreoDesercion(str, PyEnum):
    ENVIADO = "ENVIADO"
    PENDIENTE = "PENDIENTE"
    NO_APLICA = "NO_APLICA"


# ============================================================
# Tablas
# ============================================================
class Rol(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": settings.DEFAULT_SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="ck_usuarios_email"
        ),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_documento: Mapped[Optional[TipoDocumento]] = mapped_column(
        SAEnum(TipoDocumento, name="tipo_documento_t", schema=settings.DEFAULT_SCHEMA)
    )
    documento_identidad: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    rol_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.roles.id"),
        nullable=False
    )
    preferencias_ui: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class UsuarioRol(Base):
    __tablename__ = "usuario_roles"
    __table_args__ = (
        UniqueConstraint("usuario_id", "rol_id", name="uq_usuario_roles"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    rol_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.roles.id"),
        nullable=False
    )
    fecha_asignacion: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class ProgramaFormacion(Base):
    __tablename__ = "programas_formacion"
    __table_args__ = {"schema": settings.DEFAULT_SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class Ficha(Base):
    __tablename__ = "fichas"
    __table_args__ = (
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_fichas_fechas"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    programa_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.programas_formacion.id"),
        nullable=False
    )
    numero_ficha: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    fecha_inicio: Mapped[Date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[Date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class AsignacionInstructorFicha(Base):
    __tablename__ = "asignaciones_instructor_ficha"
    __table_args__ = (
        UniqueConstraint("ficha_id", "instructor_id", name="uq_asig_ficha_instructor"),
        Index("idx_asig_instructor_id", "instructor_id"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ficha_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.fichas.id"),
        nullable=False
    )
    instructor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    fecha_asignacion: Mapped[Date] = mapped_column(Date, server_default=func.current_date())
    estado_asignacion: Mapped[EstadoAsignacion] = mapped_column(
        SAEnum(EstadoAsignacion, name="estado_asignacion_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoAsignacion.ACTIVA,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class ModalidadEP(Base):
    __tablename__ = "modalidades_ep"
    __table_args__ = {"schema": settings.DEFAULT_SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class Empresa(Base):
    __tablename__ = "empresas"
    __table_args__ = {"schema": settings.DEFAULT_SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nit: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    direccion: Mapped[Optional[str]] = mapped_column(String(200))
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    correo_contacto: Mapped[Optional[str]] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class CoordinadorEmpresa(Base):
    __tablename__ = "coordinadores_empresa"
    __table_args__ = (
        Index("idx_coordinadores_empresa_empresa", "empresa_id"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.empresas.id"),
        nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    cargo: Mapped[Optional[str]] = mapped_column(String(100))
    correo: Mapped[Optional[str]] = mapped_column(String(150))
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class EvidenciaArchivo(Base):
    __tablename__ = "evidencias_archivos"
    __table_args__ = (
        CheckConstraint("tamano_bytes IS NULL OR tamano_bytes >= 0", name="ck_evidencia_tamano"),
        Index("idx_evidencias_uploaded_by", "uploaded_by"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_objeto: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo_documento: Mapped[Optional[str]] = mapped_column(String(50))
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    tamano_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class ProcesoEtapaProductiva(Base):
    __tablename__ = "procesos_etapa_productiva"
    __table_args__ = (
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_proceso_fechas"),
        CheckConstraint(
            "(empresa_id IS NULL AND coordinador_empresa_id IS NULL) OR "
            "(empresa_id IS NOT NULL AND coordinador_empresa_id IS NOT NULL)",
            name="ck_proceso_empresa_coord"
        ),
        Index("idx_procesos_aprendiz", "aprendiz_id"),
        Index("idx_procesos_ficha", "ficha_id"),
        Index("idx_procesos_modalidad", "modalidad_id"),
        Index("idx_procesos_empresa", "empresa_id"),
        Index("idx_procesos_coordinador", "coordinador_empresa_id"),
        Index("idx_procesos_instructor", "instructor_id"),
        Index("idx_procesos_estado", "estado"),
        Index("idx_procesos_estado_sofia", "estado_sofia"),
        Index("idx_procesos_estado_fecha_fin", "estado", "fecha_fin"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    aprendiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    ficha_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.fichas.id"),
        nullable=False
    )
    modalidad_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.modalidades_ep.id"),
        nullable=False
    )
    empresa_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.empresas.id")
    )
    coordinador_empresa_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.coordinadores_empresa.id")
    )
    instructor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    fecha_inicio: Mapped[Date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[Date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoProceso] = mapped_column(
        SAEnum(EstadoProceso, name="estado_proceso_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoProceso.ACTIVO,
        nullable=False
    )
    estado_sofia: Mapped[EstadoSofia] = mapped_column(
        SAEnum(EstadoSofia, name="estado_sofia_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoSofia.PENDIENTE,
        nullable=False
    )
    nota_empresa: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    nota_instructor: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class NovedadProceso(Base):
    __tablename__ = "novedades_proceso"
    __table_args__ = (
        Index("idx_novedades_proceso", "proceso_id"),
        Index("idx_novedades_tipo", "tipo_novedad"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.procesos_etapa_productiva.id"),
        nullable=False
    )
    tipo_novedad: Mapped[TipoNovedad] = mapped_column(
        SAEnum(TipoNovedad, name="tipo_novedad_t", schema=settings.DEFAULT_SCHEMA),
        nullable=False
    )
    fecha_novedad: Mapped[Date] = mapped_column(Date, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    documento_soporte_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class Charla(Base):
    __tablename__ = "charlas"
    __table_args__ = (
        UniqueConstraint("ficha_id", "tipo_charla", name="uq_charlas_ficha_tipo"),
        Index("idx_charlas_instructor", "instructor_id"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ficha_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.fichas.id"),
        nullable=False
    )
    tipo_charla: Mapped[TipoCharla] = mapped_column(
        SAEnum(TipoCharla, name="tipo_charla_t", schema=settings.DEFAULT_SCHEMA),
        nullable=False
    )
    fecha_programada: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    instructor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    tema: Mapped[Optional[str]] = mapped_column(String(200))
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class AsistenciaCharla(Base):
    __tablename__ = "asistencias_charlas"
    __table_args__ = (
        UniqueConstraint("charla_id", "aprendiz_id", name="uq_asistencia_charla_aprendiz"),
        CheckConstraint("asistio = FALSE OR fecha_asistencia IS NOT NULL", name="ck_asistencia_fecha"),
        Index("idx_asistencias_aprendiz", "aprendiz_id"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    charla_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.charlas.id"),
        nullable=False
    )
    aprendiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    asistio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_asistencia: Mapped[Optional[Date]] = mapped_column(Date)
    evidencia_archivo_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.evidencias_archivos.id")
    )
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class ReunionSeguimiento(Base):
    __tablename__ = "reuniones_seguimiento"
    __table_args__ = (
        UniqueConstraint("proceso_id", "momento", name="uq_reunion_proceso_momento"),
        CheckConstraint(
            "fecha_realizada IS NULL OR fecha_realizada >= fecha_programada",
            name="ck_reunion_fechas"
        ),
        CheckConstraint(
            "fecha_realizada IS NULL OR (evidencia_archivo_id IS NOT NULL OR archivo_f023_url IS NOT NULL)",
            name="ck_reunion_evidencia_realizada"
        ),
        Index("idx_reuniones_instructor", "instructor_id"),
        Index("idx_reuniones_proceso", "proceso_id"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.procesos_etapa_productiva.id"),
        nullable=False
    )
    momento: Mapped[MomentoReunion] = mapped_column(
        SAEnum(MomentoReunion, name="momento_reunion_t", schema=settings.DEFAULT_SCHEMA),
        nullable=False
    )
    fecha_programada: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_realizada: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    instructor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    evidencia_archivo_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.evidencias_archivos.id")
    )
    archivo_f023_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class Bitacora(Base):
    __tablename__ = "bitacoras"
    __table_args__ = (
        CheckConstraint("periodo_reportado ~ '^\\d{4}-\\d{2}$'", name="ck_bitacora_periodo"),
        CheckConstraint("estado = 'BORRADOR' OR fecha_envio IS NOT NULL", name="ck_bitacora_envio"),
        CheckConstraint("numero_bitacora > 0", name="ck_bitacora_numero_positivo"),
        UniqueConstraint("proceso_id", "numero_bitacora", name="uq_bitacora_proceso_numero"),
        Index("idx_bitacoras_proceso", "proceso_id"),
        Index("idx_bitacoras_estado", "estado"),
        Index("idx_bitacoras_periodo", "periodo_reportado"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.procesos_etapa_productiva.id"),
        nullable=False
    )
    numero_bitacora: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo_reportado: Mapped[str] = mapped_column(String(7), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoBitacora] = mapped_column(
        SAEnum(EstadoBitacora, name="estado_bitacora_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoBitacora.BORRADOR,
        nullable=False
    )
    fecha_envio: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    instructor_retroalimentacion: Mapped[Optional[str]] = mapped_column(Text)
    fecha_revision: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    archivo_f147_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class BitacoraEvidencia(Base):
    __tablename__ = "bitacora_evidencias"
    __table_args__ = (
        UniqueConstraint("bitacora_id", "evidencia_archivo_id", name="uq_bitacora_evidencia"),
        Index("idx_bitacora_evid_archivo", "evidencia_archivo_id"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bitacora_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.bitacoras.id"),
        nullable=False
    )
    evidencia_archivo_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.evidencias_archivos.id"),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class NotificacionMensaje(Base):
    __tablename__ = "notificaciones_mensajes"
    __table_args__ = (
        Index("idx_notif_destinatario", "destinatario_usuario_id"),
        Index("idx_notif_estado_envio", "estado_envio_email"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    remitente_usuario_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id")
    )
    destinatario_usuario_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=False
    )
    asunto: Mapped[str] = mapped_column(String(200), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_creacion: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_envio_email: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    estado_envio_email: Mapped[EstadoEnvioEmail] = mapped_column(
        SAEnum(EstadoEnvioEmail, name="estado_envio_email_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoEnvioEmail.PENDIENTE,
        nullable=False
    )
    error_envio: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class ChecklistDocumentoProceso(Base):
    __tablename__ = "checklist_documentos_proceso"
    __table_args__ = (
        UniqueConstraint("proceso_id", "tipo_documento", name="uq_checklist_proceso_tipo"),
        Index("idx_checklist_proceso", "proceso_id"),
        Index("idx_checklist_estado", "estado"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.procesos_etapa_productiva.id"),
        nullable=False
    )
    tipo_documento: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[EstadoDocumento] = mapped_column(
        SAEnum(EstadoDocumento, name="estado_documento_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoDocumento.PENDIENTE,
        nullable=False
    )
    evidencia_archivo_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.evidencias_archivos.id")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class MedidasFormativasProceso(Base):
    __tablename__ = "medidas_formativas_proceso"
    __table_args__ = (
        UniqueConstraint("proceso_id", name="uq_medidas_proceso"),
        CheckConstraint(
            "llamado_atencion_estado <> 'SI' OR fecha_llamado_atencion IS NOT NULL",
            name="ck_llamado_fecha"
        ),
        CheckConstraint(
            "plan_mejoramiento_estado <> 'SI' OR fecha_plan_mejoramiento IS NOT NULL",
            name="ck_plan_fecha"
        ),
        CheckConstraint(
            "correo_desercion_1_estado <> 'ENVIADO' OR fecha_correo_desercion_1 IS NOT NULL",
            name="ck_correo1_fecha"
        ),
        CheckConstraint(
            "correo_desercion_2_estado <> 'ENVIADO' OR fecha_correo_desercion_2 IS NOT NULL",
            name="ck_correo2_fecha"
        ),
        Index("idx_medidas_proceso", "proceso_id"),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    proceso_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.procesos_etapa_productiva.id"),
        nullable=False
    )
    llamado_atencion_estado: Mapped[EstadoMedidaFormativa] = mapped_column(
        SAEnum(EstadoMedidaFormativa, name="estado_medida_formativa_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoMedidaFormativa.PENDIENTE,
        nullable=False
    )
    plan_mejoramiento_estado: Mapped[EstadoMedidaFormativa] = mapped_column(
        SAEnum(EstadoMedidaFormativa, name="estado_medida_formativa_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoMedidaFormativa.PENDIENTE,
        nullable=False
    )
    correo_desercion_1_estado: Mapped[EstadoCorreoDesercion] = mapped_column(
        SAEnum(EstadoCorreoDesercion, name="estado_correo_desercion_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoCorreoDesercion.NO_APLICA,
        nullable=False
    )
    correo_desercion_2_estado: Mapped[EstadoCorreoDesercion] = mapped_column(
        SAEnum(EstadoCorreoDesercion, name="estado_correo_desercion_t", schema=settings.DEFAULT_SCHEMA),
        default=EstadoCorreoDesercion.NO_APLICA,
        nullable=False
    )
    fecha_llamado_atencion: Mapped[Optional[Date]] = mapped_column(Date)
    fecha_plan_mejoramiento: Mapped[Optional[Date]] = mapped_column(Date)
    fecha_correo_desercion_1: Mapped[Optional[Date]] = mapped_column(Date)
    fecha_correo_desercion_2: Mapped[Optional[Date]] = mapped_column(Date)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = (
        CheckConstraint(
            "accion IN ('INSERT', 'UPDATE', 'DELETE')",
            name="ck_auditoria_accion"
        ),
        {"schema": settings.DEFAULT_SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tabla: Mapped[str] = mapped_column(String(100), nullable=False)
    registro_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    usuario_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("etapa_productiva.usuarios.id"),
        nullable=True,
    )
    accion: Mapped[str] = mapped_column(String(20), nullable=False)
    datos_anteriores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    datos_nuevos: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )