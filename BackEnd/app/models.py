from sqlalchemy import (
    Column, BigInteger, String, Text, Boolean, DateTime, Date, 
    Numeric, ForeignKey, CheckConstraint, UniqueConstraint,
    JSON, Integer, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class EstadoBitacora(str, Enum):
    BORRADOR = "BORRADOR"
    ENVIADA = "ENVIADA"
    APROBADA = "APROBADA"
    CON_OBSERVACIONES = "CON_OBSERVACIONES"

class MomentoReunion(str, Enum):
    MOMENTO_1_INICIAL = "MOMENTO_1_INICIAL"
    MOMENTO_2_PARCIAL = "MOMENTO_2_PARCIAL"
    MOMENTO_3_FINAL = "MOMENTO_3_FINAL"

class TipoCharla(str, Enum):
    CHARLA_INICIAL = "CHARLA_INICIAL"
    CHARLA_PRE_PRODUCTIVA = "CHARLA_PRE_PRODUCTIVA"

class EstadoProceso(str, Enum):
    ACTIVO = "ACTIVO"
    FINALIZADO = "FINALIZADO"
    APLAZADO = "APLAZADO"
    RETIRADO = "RETIRADO"

class EstadoSofia(str, Enum):
    PENDIENTE = "PENDIENTE"
    POR_EVALUAR = "POR_EVALUAR"
    APROBADO = "APROBADO"
    NO_APROBADO = "NO_APROBADO"

class TipoNovedad(str, Enum):
    RENUNCIA = "RENUNCIA"
    INCAPACIDAD = "INCAPACIDAD"
    CAMBIO_EMPRESA = "CAMBIO_EMPRESA"
    PRORROGA = "PRORROGA"
    OTRO = "OTRO"

class EstadoEnvioEmail(str, Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    ERROR = "ERROR"

class EstadoAsignacion(str, Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"

class TipoDocumento(str, Enum):
    TI = "TI"
    CC = "CC"
    CE = "CE"
    PTE = "PTE"

class EstadoDocumento(str, Enum):
    ENTREGADO = "ENTREGADO"
    PENDIENTE = "PENDIENTE"
    NO_APLICA = "NO_APLICA"

class EstadoMedidaFormativa(str, Enum):
    SI = "SI"
    NO = "NO"
    PENDIENTE = "PENDIENTE"

class EstadoCorreoDesercion(str, Enum):
    ENVIADO = "ENVIADO"
    PENDIENTE = "PENDIENTE"
    NO_APLICA = "NO_APLICA"


# ============================================================
# TABLAS
# ============================================================

class Rol(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name="ck_usuarios_email"),
        Index("idx_usuarios_email_active", "email"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    tipo_documento = Column(ENUM('TI', 'CC', 'CE', 'PTE', name='tipo_documento_t', schema='etapa_productiva'))
    documento_identidad = Column(String(20), unique=True)
    telefono = Column(String(20))
    rol_id = Column(BigInteger, ForeignKey("etapa_productiva.roles.id"), nullable=False)
    preferencias_ui = Column(JSON, nullable=False, server_default='{}')
    is_active = Column(Boolean, default=True, nullable=False)
    reset_code = Column(String(6), nullable=True)
    reset_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    rol = relationship("Rol", foreign_keys=[rol_id])


class ProgramaFormacion(Base):
    __tablename__ = "programas_formacion"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    codigo = Column(String(30), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class Ficha(Base):
    __tablename__ = "fichas"
    __table_args__ = (
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_fichas_fechas"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    programa_id = Column(BigInteger, ForeignKey("etapa_productiva.programas_formacion.id"), nullable=False)
    numero_ficha = Column(String(20), nullable=False, unique=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    nivel = Column(String(50), default='Tecnólogo')
    jornada = Column(String(50), default='Mañana')
    aprendices_esperados = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class AsignacionInstructorFicha(Base):
    __tablename__ = "asignaciones_instructor_ficha"
    __table_args__ = (
        UniqueConstraint("ficha_id", "instructor_id", name="uq_asig_ficha_instructor"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    ficha_id = Column(BigInteger, ForeignKey("etapa_productiva.fichas.id"), nullable=False)
    instructor_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"), nullable=False)
    fecha_asignacion = Column(Date, server_default=func.current_date())
    estado_asignacion = Column(ENUM('ACTIVA', 'INACTIVA', name='estado_asignacion_t', schema='etapa_productiva'), default='ACTIVA')
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 🔥 FIX: se agregó server_default=func.now()
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class ModalidadEP(Base):
    __tablename__ = "modalidades_ep"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class Empresa(Base):
    __tablename__ = "empresas"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    nit = Column(String(20), unique=True, nullable=False)
    razon_social = Column(String(200), nullable=False)
    direccion = Column(String(200))
    telefono = Column(String(20))
    correo_contacto = Column(String(150))
    arl = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class CoordinadorEmpresa(Base):
    __tablename__ = "coordinadores_empresa"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    empresa_id = Column(BigInteger, ForeignKey("etapa_productiva.empresas.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    cargo = Column(String(100))
    correo = Column(String(150))
    telefono = Column(String(20))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class EvidenciaArchivo(Base):
    __tablename__ = "evidencias_archivos"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_objeto = Column(String(500), nullable=False)
    tipo_documento = Column(String(50))
    mime_type = Column(String(100))
    tamano_bytes = Column(BigInteger)
    uploaded_by = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class ProcesoEtapaProductiva(Base):
    __tablename__ = "procesos_etapa_productiva"
    __table_args__ = (
        CheckConstraint('fecha_fin >= fecha_inicio', name='ck_proceso_fechas'),
        CheckConstraint(
            '(empresa_id IS NULL AND coordinador_empresa_id IS NULL) OR (empresa_id IS NOT NULL AND coordinador_empresa_id IS NOT NULL)',
            name='ck_proceso_empresa_coord'
        ),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    aprendiz_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"), nullable=False)
    ficha_id = Column(BigInteger, ForeignKey("etapa_productiva.fichas.id"), nullable=False)
    modalidad_id = Column(BigInteger, ForeignKey("etapa_productiva.modalidades_ep.id"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("etapa_productiva.empresas.id"), nullable=True)
    coordinador_empresa_id = Column(BigInteger, ForeignKey("etapa_productiva.coordinadores_empresa.id"), nullable=True)
    instructor_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(ENUM('ACTIVO', 'FINALIZADO', 'APLAZADO', 'RETIRADO', name='estado_proceso_t', schema='etapa_productiva'), default='ACTIVO')
    estado_sofia = Column(ENUM('PENDIENTE', 'POR_EVALUAR', 'APROBADO', 'NO_APROBADO', name='estado_sofia_t', schema='etapa_productiva'), default='PENDIENTE')
    nota_empresa = Column(Numeric(3, 1))
    nota_instructor = Column(Numeric(3, 1))
    observaciones = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))

    # Relaciones
    aprendiz = relationship("Usuario", foreign_keys=[aprendiz_id])
    instructor = relationship("Usuario", foreign_keys=[instructor_id])
    empresa = relationship("Empresa", foreign_keys=[empresa_id])
    ficha = relationship("Ficha", foreign_keys=[ficha_id])

    # ---- Propiedades calculadas para el frontend ----
    @property
    def aprendiz_nombre(self) -> str | None:
        if self.aprendiz:
            return f"{self.aprendiz.nombre} {self.aprendiz.apellido}".strip()
        return None

    @property
    def aprendiz_email(self) -> str | None:
        return self.aprendiz.email if self.aprendiz else None

    @property
    def aprendiz_documento(self) -> str | None:
        if self.aprendiz and self.aprendiz.documento_identidad:
            tipo = self.aprendiz.tipo_documento
            tipo_str = tipo.value if hasattr(tipo, 'value') else (tipo or '')
            return f"{tipo_str} {self.aprendiz.documento_identidad}".strip()
        return None

    @property
    def aprendiz_telefono(self) -> str | None:
        return self.aprendiz.telefono if self.aprendiz else None

    @property
    def empresa_nombre(self) -> str | None:
        return self.empresa.razon_social if self.empresa else None

    @property
    def arl(self) -> str | None:
        return self.empresa.arl if self.empresa else None

    @property
    def ficha_numero(self) -> str | None:
        return self.ficha.numero_ficha if self.ficha else None


class Bitacora(Base):
    __tablename__ = "bitacoras"
    __table_args__ = (
        CheckConstraint("periodo_reportado ~ '^\\d{4}-\\d{2}$'", name='ck_bitacora_periodo'),
        CheckConstraint("estado = 'BORRADOR' OR fecha_envio IS NOT NULL", name='ck_bitacora_envio'),
        CheckConstraint("numero_bitacora > 0", name='ck_bitacora_numero_positivo'),
        UniqueConstraint("proceso_id", "numero_bitacora", name='uq_bitacora_proceso_numero'),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    proceso_id = Column(BigInteger, ForeignKey("etapa_productiva.procesos_etapa_productiva.id", ondelete="CASCADE"), nullable=False)
    numero_bitacora = Column(Integer, nullable=False)
    periodo_reportado = Column(String(7), nullable=False)
    titulo = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)
    estado = Column(ENUM('BORRADOR', 'ENVIADA', 'APROBADA', 'CON_OBSERVACIONES', name='estado_bitacora_t', schema='etapa_productiva'), default='BORRADOR')
    fecha_envio = Column(DateTime(timezone=True), nullable=True)
    instructor_retroalimentacion = Column(Text)
    fecha_revision = Column(DateTime(timezone=True), nullable=True)
    archivo_f147_url = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    proceso = relationship("ProcesoEtapaProductiva", foreign_keys=[proceso_id])


class Charla(Base):
    __tablename__ = "charlas"
    __table_args__ = (
        UniqueConstraint("ficha_id", "tipo_charla", name="uq_charlas_ficha_tipo"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    ficha_id = Column(BigInteger, ForeignKey("etapa_productiva.fichas.id"), nullable=False)
    tipo_charla = Column(ENUM('CHARLA_INICIAL', 'CHARLA_PRE_PRODUCTIVA', name='tipo_charla_t', schema='etapa_productiva'), nullable=False)
    fecha_programada = Column(DateTime(timezone=True), nullable=False)
    instructor_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"), nullable=False)
    tema = Column(String(200))
    created_by = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class AsistenciaCharla(Base):
    __tablename__ = "asistencias_charlas"
    __table_args__ = (
        UniqueConstraint("charla_id", "aprendiz_id", name="uq_asistencia_charla_aprendiz"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    charla_id = Column(BigInteger, ForeignKey("etapa_productiva.charlas.id"), nullable=False)
    aprendiz_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"), nullable=False)
    asistio = Column(Boolean, default=False, nullable=False)
    fecha_asistencia = Column(Date)
    evidencia_archivo_id = Column(BigInteger, ForeignKey("etapa_productiva.evidencias_archivos.id"))
    observaciones = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class ReunionSeguimiento(Base):
    __tablename__ = "reuniones_seguimiento"
    __table_args__ = (
        UniqueConstraint("proceso_id", "momento", name="uq_reunion_proceso_momento"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    proceso_id = Column(BigInteger, ForeignKey("etapa_productiva.procesos_etapa_productiva.id"), nullable=False)
    momento = Column(ENUM('MOMENTO_1_INICIAL', 'MOMENTO_2_PARCIAL', 'MOMENTO_3_FINAL', name='momento_reunion_t', schema='etapa_productiva'), nullable=False)
    fecha_programada = Column(DateTime(timezone=True), nullable=False)
    fecha_realizada = Column(DateTime(timezone=True), nullable=True)
    instructor_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"), nullable=False)
    observaciones = Column(Text)
    evidencia_archivo_id = Column(BigInteger, ForeignKey("etapa_productiva.evidencias_archivos.id"))
    archivo_f023_url = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class NovedadProceso(Base):
    __tablename__ = "novedades_proceso"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    proceso_id = Column(BigInteger, ForeignKey("etapa_productiva.procesos_etapa_productiva.id"), nullable=False)
    tipo_novedad = Column(ENUM('RENUNCIA', 'INCAPACIDAD', 'CAMBIO_EMPRESA', 'PRORROGA', 'OTRO', name='tipo_novedad_t', schema='etapa_productiva'), nullable=False)
    fecha_novedad = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    documento_soporte_url = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class ChecklistDocumentoProceso(Base):
    __tablename__ = "checklist_documentos_proceso"
    __table_args__ = (
        UniqueConstraint("proceso_id", "tipo_documento", name="uq_checklist_proceso_tipo"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    proceso_id = Column(BigInteger, ForeignKey("etapa_productiva.procesos_etapa_productiva.id"), nullable=False)
    tipo_documento = Column(String(50), nullable=False)
    estado = Column(ENUM('ENTREGADO', 'PENDIENTE', 'NO_APLICA', name='estado_documento_t', schema='etapa_productiva'), default='PENDIENTE')
    evidencia_archivo_id = Column(BigInteger, ForeignKey("etapa_productiva.evidencias_archivos.id"))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class MedidasFormativasProceso(Base):
    __tablename__ = "medidas_formativas_proceso"
    __table_args__ = (
        UniqueConstraint("proceso_id", name="uq_medidas_proceso"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    proceso_id = Column(BigInteger, ForeignKey("etapa_productiva.procesos_etapa_productiva.id"), nullable=False)
    llamado_atencion_estado = Column(ENUM('SI', 'NO', 'PENDIENTE', name='estado_medida_formativa_t', schema='etapa_productiva'), default='PENDIENTE')
    plan_mejoramiento_estado = Column(ENUM('SI', 'NO', 'PENDIENTE', name='estado_medida_formativa_t', schema='etapa_productiva'), default='PENDIENTE')
    correo_desercion_1_estado = Column(ENUM('ENVIADO', 'PENDIENTE', 'NO_APLICA', name='estado_correo_desercion_t', schema='etapa_productiva'), default='NO_APLICA')
    correo_desercion_2_estado = Column(ENUM('ENVIADO', 'PENDIENTE', 'NO_APLICA', name='estado_correo_desercion_t', schema='etapa_productiva'), default='NO_APLICA')
    fecha_llamado_atencion = Column(Date)
    fecha_plan_mejoramiento = Column(Date)
    fecha_correo_desercion_1 = Column(Date)
    fecha_correo_desercion_2 = Column(Date)
    observaciones = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class NotificacionMensaje(Base):
    __tablename__ = "notificaciones_mensajes"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    remitente_usuario_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"))
    destinatario_usuario_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"), nullable=False)
    asunto = Column(String(200), nullable=False)
    cuerpo = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_envio_email = Column(DateTime(timezone=True))
    estado_envio_email = Column(ENUM('PENDIENTE', 'ENVIADO', 'ERROR', name='estado_envio_email_t', schema='etapa_productiva'), default='PENDIENTE')
    error_envio = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class BitacoraEvidencia(Base):
    __tablename__ = "bitacora_evidencias"
    __table_args__ = (
        UniqueConstraint("bitacora_id", "evidencia_archivo_id", name="uq_bitacora_evidencia"),
        {"schema": "etapa_productiva"},
    )
    id = Column(BigInteger, primary_key=True)
    bitacora_id = Column(BigInteger, ForeignKey("etapa_productiva.bitacoras.id"), nullable=False)
    evidencia_archivo_id = Column(BigInteger, ForeignKey("etapa_productiva.evidencias_archivos.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = {"schema": "etapa_productiva"}
    id = Column(BigInteger, primary_key=True)
    tabla = Column(String(100), nullable=False)
    registro_id = Column(BigInteger, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey("etapa_productiva.usuarios.id"))
    accion = Column(String(20), nullable=False)
    datos_anteriores = Column(JSON)
    datos_nuevos = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())