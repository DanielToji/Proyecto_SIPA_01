-- ============================================================
-- SCRIPT COMPLETO - SIPA (Corregido + Seeds + Verificación)
-- ============================================================

DROP SCHEMA IF EXISTS etapa_productiva CASCADE;
CREATE SCHEMA etapa_productiva;
SET search_path TO etapa_productiva;

-- ============================================================
-- 1. TIPOS ENUM
-- ============================================================
CREATE TYPE estado_bitacora_t AS ENUM ('BORRADOR', 'ENVIADA', 'APROBADA', 'CON_OBSERVACIONES');
CREATE TYPE momento_reunion_t AS ENUM ('MOMENTO_1_INICIAL', 'MOMENTO_2_PARCIAL', 'MOMENTO_3_FINAL');
CREATE TYPE tipo_charla_t AS ENUM ('CHARLA_INICIAL', 'CHARLA_PRE_PRODUCTIVA');
CREATE TYPE estado_proceso_t AS ENUM ('ACTIVO', 'FINALIZADO', 'APLAZADO', 'RETIRADO');
CREATE TYPE estado_sofia_t AS ENUM ('PENDIENTE', 'POR_EVALUAR', 'APROBADO', 'NO_APROBADO');
CREATE TYPE tipo_novedad_t AS ENUM ('RENUNCIA', 'INCAPACIDAD', 'CAMBIO_EMPRESA', 'PRORROGA', 'OTRO');
CREATE TYPE estado_envio_email_t AS ENUM ('PENDIENTE', 'ENVIADO', 'ERROR');
CREATE TYPE estado_asignacion_t AS ENUM ('ACTIVA', 'INACTIVA');
CREATE TYPE tipo_documento_t AS ENUM ('TI', 'CC', 'CE', 'PTE');
CREATE TYPE estado_documento_t AS ENUM ('ENTREGADO', 'PENDIENTE', 'NO_APLICA');
CREATE TYPE estado_medida_formativa_t AS ENUM ('SI', 'NO', 'PENDIENTE');
CREATE TYPE estado_correo_desercion_t AS ENUM ('ENVIADO', 'PENDIENTE', 'NO_APLICA');

-- ============================================================
-- 2. FUNCIÓN DE AUDITORÍA (Triggers)
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 3. TABLAS BASE: SEGURIDAD Y ACADÉMICAS
-- ============================================================
CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE usuarios (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    tipo_documento tipo_documento_t,
    documento_identidad VARCHAR(20) UNIQUE,
    telefono VARCHAR(20),
    rol_id BIGINT NOT NULL,
    preferencias_ui JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_usuarios_rol FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE RESTRICT,
    CONSTRAINT ck_usuarios_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Columnas necesarias para recuperación de contraseña
ALTER TABLE usuarios ADD COLUMN reset_code VARCHAR(6);
ALTER TABLE usuarios ADD COLUMN reset_code_expires_at TIMESTAMPTZ;

CREATE TABLE usuario_roles (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    rol_id BIGINT NOT NULL,
    fecha_asignacion TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_usuario_roles_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_usuario_roles_rol FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE RESTRICT,
    CONSTRAINT uq_usuario_roles UNIQUE (usuario_id, rol_id)
);

CREATE TABLE programas_formacion (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE fichas (
    id BIGSERIAL PRIMARY KEY,
    programa_id BIGINT NOT NULL,
    numero_ficha VARCHAR(20) NOT NULL UNIQUE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_fichas_programa FOREIGN KEY (programa_id) REFERENCES programas_formacion(id) ON DELETE RESTRICT,
    CONSTRAINT ck_fichas_fechas CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE asignaciones_instructor_ficha (
    id BIGSERIAL PRIMARY KEY,
    ficha_id BIGINT NOT NULL,
    instructor_id BIGINT NOT NULL,
    fecha_asignacion DATE NOT NULL DEFAULT CURRENT_DATE,
    estado_asignacion estado_asignacion_t NOT NULL DEFAULT 'ACTIVA',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_asig_ficha FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE,
    CONSTRAINT fk_asig_instructor FOREIGN KEY (instructor_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT uq_asig_ficha_instructor UNIQUE (ficha_id, instructor_id)
);

-- ============================================================
-- 4. TABLAS: EMPRESAS Y MODALIDADES
-- ============================================================
CREATE TABLE modalidades_ep (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE empresas (
    id BIGSERIAL PRIMARY KEY,
    nit VARCHAR(20) NOT NULL UNIQUE,
    razon_social VARCHAR(200) NOT NULL,
    direccion VARCHAR(200),
    telefono VARCHAR(20),
    correo_contacto VARCHAR(150),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE coordinadores_empresa (
    id BIGSERIAL PRIMARY KEY,
    empresa_id BIGINT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    cargo VARCHAR(100),
    correo VARCHAR(150),
    telefono VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_coord_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

-- ============================================================
-- 5. TABLA: EVIDENCIAS / ARCHIVOS (Metadata)
-- ============================================================
CREATE TABLE evidencias_archivos (
    id BIGSERIAL PRIMARY KEY,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_objeto VARCHAR(500) NOT NULL,
    tipo_documento VARCHAR(50),
    mime_type VARCHAR(100),
    tamano_bytes BIGINT,
    uploaded_by BIGINT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_evidencia_uploader FOREIGN KEY (uploaded_by) REFERENCES usuarios(id) ON DELETE SET NULL,
    CONSTRAINT ck_evidencia_tamano CHECK (tamano_bytes IS NULL OR tamano_bytes >= 0)
);

-- ============================================================
-- 6. TABLA CORE: PROCESOS DE ETAPA PRODUCTIVA
-- ============================================================
CREATE TABLE procesos_etapa_productiva (
    id BIGSERIAL PRIMARY KEY,
    aprendiz_id BIGINT NOT NULL,
    ficha_id BIGINT NOT NULL,
    modalidad_id BIGINT NOT NULL,
    empresa_id BIGINT,
    coordinador_empresa_id BIGINT,
    instructor_id BIGINT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado estado_proceso_t NOT NULL DEFAULT 'ACTIVO',
    estado_sofia estado_sofia_t NOT NULL DEFAULT 'PENDIENTE',
    nota_empresa NUMERIC(3,1) CHECK (nota_empresa BETWEEN 0 AND 10),
    nota_instructor NUMERIC(3,1) CHECK (nota_instructor BETWEEN 0 AND 10),
    observaciones TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_proceso_aprendiz FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_proceso_ficha FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_proceso_modalidad FOREIGN KEY (modalidad_id) REFERENCES modalidades_ep(id) ON DELETE RESTRICT,
    CONSTRAINT fk_proceso_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_proceso_coordinador FOREIGN KEY (coordinador_empresa_id) REFERENCES coordinadores_empresa(id) ON DELETE RESTRICT,
    CONSTRAINT fk_proceso_instructor FOREIGN KEY (instructor_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT ck_proceso_fechas CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT ck_proceso_empresa_coord CHECK (
        (empresa_id IS NULL AND coordinador_empresa_id IS NULL) OR
        (empresa_id IS NOT NULL AND coordinador_empresa_id IS NOT NULL)
    )
);

-- ============================================================
-- 7. TABLAS DE SEGUIMIENTO (Formatos F023, F147 y Novedades)
-- ============================================================
CREATE TABLE reuniones_seguimiento (
    id BIGSERIAL PRIMARY KEY,
    proceso_id BIGINT NOT NULL,
    momento momento_reunion_t NOT NULL,
    fecha_programada TIMESTAMPTZ NOT NULL,
    fecha_realizada TIMESTAMPTZ,
    instructor_id BIGINT NOT NULL,
    observaciones TEXT,
    evidencia_archivo_id BIGINT,
    archivo_f023_url VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_reunion_proceso FOREIGN KEY (proceso_id) REFERENCES procesos_etapa_productiva(id) ON DELETE CASCADE,
    CONSTRAINT fk_reunion_instructor FOREIGN KEY (instructor_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reunion_evidencia FOREIGN KEY (evidencia_archivo_id) REFERENCES evidencias_archivos(id) ON DELETE SET NULL,
    CONSTRAINT uq_reunion_proceso_momento UNIQUE (proceso_id, momento),
    CONSTRAINT ck_reunion_fechas CHECK (fecha_realizada IS NULL OR fecha_realizada >= fecha_programada),
    CONSTRAINT ck_reunion_evidencia_realizada CHECK (
        fecha_realizada IS NULL OR (evidencia_archivo_id IS NOT NULL OR archivo_f023_url IS NOT NULL)
    )
);

CREATE TABLE bitacoras (
    id BIGSERIAL PRIMARY KEY,
    proceso_id BIGINT NOT NULL,
    numero_bitacora INTEGER NOT NULL,
    periodo_reportado VARCHAR(7) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    contenido TEXT NOT NULL,
    estado estado_bitacora_t NOT NULL DEFAULT 'BORRADOR',
    fecha_envio TIMESTAMPTZ,
    instructor_retroalimentacion TEXT,
    fecha_revision TIMESTAMPTZ,
    archivo_f147_url VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_bitacora_proceso FOREIGN KEY (proceso_id) REFERENCES procesos_etapa_productiva(id) ON DELETE CASCADE,
    CONSTRAINT ck_bitacora_periodo CHECK (periodo_reportado ~ '^\d{4}-\d{2}$'),
    CONSTRAINT ck_bitacora_envio CHECK (estado = 'BORRADOR' OR fecha_envio IS NOT NULL),
    CONSTRAINT ck_bitacora_numero_positivo CHECK (numero_bitacora > 0),
    CONSTRAINT uq_bitacora_proceso_numero UNIQUE (proceso_id, numero_bitacora)
);

CREATE TABLE bitacora_evidencias (
    id BIGSERIAL PRIMARY KEY,
    bitacora_id BIGINT NOT NULL,
    evidencia_archivo_id BIGINT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_bitacora_evid_bitacora FOREIGN KEY (bitacora_id) REFERENCES bitacoras(id) ON DELETE CASCADE,
    CONSTRAINT fk_bitacora_evid_archivo FOREIGN KEY (evidencia_archivo_id) REFERENCES evidencias_archivos(id) ON DELETE CASCADE,
    CONSTRAINT uq_bitacora_evidencia UNIQUE (bitacora_id, evidencia_archivo_id)
);

CREATE TABLE novedades_proceso (
    id BIGSERIAL PRIMARY KEY,
    proceso_id BIGINT NOT NULL,
    tipo_novedad tipo_novedad_t NOT NULL,
    fecha_novedad DATE NOT NULL,
    descripcion TEXT NOT NULL,
    documento_soporte_url VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_novedad_proceso FOREIGN KEY (proceso_id) REFERENCES procesos_etapa_productiva(id) ON DELETE CASCADE
);

-- ============================================================
-- 8. NUEVAS TABLAS: CHECKLIST DOCUMENTAL Y MEDIDAS FORMATIVAS
-- ============================================================
CREATE TABLE checklist_documentos_proceso (
    id BIGSERIAL PRIMARY KEY,
    proceso_id BIGINT NOT NULL REFERENCES procesos_etapa_productiva(id) ON DELETE CASCADE,
    tipo_documento VARCHAR(50) NOT NULL,
    estado estado_documento_t NOT NULL DEFAULT 'PENDIENTE',
    evidencia_archivo_id BIGINT REFERENCES evidencias_archivos(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT uq_checklist_proceso_tipo UNIQUE (proceso_id, tipo_documento)
);

CREATE TABLE medidas_formativas_proceso (
    id BIGSERIAL PRIMARY KEY,
    proceso_id BIGINT NOT NULL REFERENCES procesos_etapa_productiva(id) ON DELETE CASCADE,
    llamado_atencion_estado estado_medida_formativa_t NOT NULL DEFAULT 'PENDIENTE',
    plan_mejoramiento_estado estado_medida_formativa_t NOT NULL DEFAULT 'PENDIENTE',
    correo_desercion_1_estado estado_correo_desercion_t NOT NULL DEFAULT 'NO_APLICA',
    correo_desercion_2_estado estado_correo_desercion_t NOT NULL DEFAULT 'NO_APLICA',
    fecha_llamado_atencion DATE,
    fecha_plan_mejoramiento DATE,
    fecha_correo_desercion_1 DATE,
    fecha_correo_desercion_2 DATE,
    observaciones TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT uq_medidas_proceso UNIQUE (proceso_id),
    CONSTRAINT ck_llamado_fecha CHECK (llamado_atencion_estado <> 'SI' OR fecha_llamado_atencion IS NOT NULL),
    CONSTRAINT ck_plan_fecha CHECK (plan_mejoramiento_estado <> 'SI' OR fecha_plan_mejoramiento IS NOT NULL),
    CONSTRAINT ck_correo1_fecha CHECK (correo_desercion_1_estado <> 'ENVIADO' OR fecha_correo_desercion_1 IS NOT NULL),
    CONSTRAINT ck_correo2_fecha CHECK (correo_desercion_2_estado <> 'ENVIADO' OR fecha_correo_desercion_2 IS NOT NULL)
);

-- ============================================================
-- 9. TABLAS: CHARLAS Y ASISTENCIAS (Pre-productiva)
-- ============================================================
CREATE TABLE charlas (
    id BIGSERIAL PRIMARY KEY,
    ficha_id BIGINT NOT NULL,
    tipo_charla tipo_charla_t NOT NULL,
    fecha_programada TIMESTAMPTZ NOT NULL,
    instructor_id BIGINT NOT NULL,
    tema VARCHAR(200),
    created_by BIGINT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_charlas_ficha FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE,
    CONSTRAINT fk_charlas_instructor FOREIGN KEY (instructor_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_charlas_created_by FOREIGN KEY (created_by) REFERENCES usuarios(id) ON DELETE SET NULL,
    CONSTRAINT uq_charlas_ficha_tipo UNIQUE (ficha_id, tipo_charla)
);

CREATE TABLE asistencias_charlas (
    id BIGSERIAL PRIMARY KEY,
    charla_id BIGINT NOT NULL,
    aprendiz_id BIGINT NOT NULL,
    asistio BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_asistencia DATE,
    evidencia_archivo_id BIGINT,
    observaciones TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_asistencia_charla FOREIGN KEY (charla_id) REFERENCES charlas(id) ON DELETE CASCADE,
    CONSTRAINT fk_asistencia_aprendiz FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_asistencia_evidencia FOREIGN KEY (evidencia_archivo_id) REFERENCES evidencias_archivos(id) ON DELETE SET NULL,
    CONSTRAINT uq_asistencia_charla_aprendiz UNIQUE (charla_id, aprendiz_id),
    CONSTRAINT ck_asistencia_fecha CHECK (asistio = FALSE OR fecha_asistencia IS NOT NULL)
);

-- ============================================================
-- 10. TABLAS: COMUNICACIONES
-- ============================================================
CREATE TABLE notificaciones_mensajes (
    id BIGSERIAL PRIMARY KEY,
    remitente_usuario_id BIGINT,
    destinatario_usuario_id BIGINT NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    cuerpo TEXT NOT NULL,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT now(),
    fecha_envio_email TIMESTAMPTZ,
    estado_envio_email estado_envio_email_t NOT NULL DEFAULT 'PENDIENTE',
    error_envio TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_notif_remitente FOREIGN KEY (remitente_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    CONSTRAINT fk_notif_destinatario FOREIGN KEY (destinatario_usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ============================================================
-- 11. ÍNDICES PARA ALTO TRÁFICO
-- ============================================================
CREATE INDEX idx_usuario_roles_rol ON usuario_roles(rol_id);
CREATE INDEX idx_usuarios_email_active ON usuarios(email) WHERE is_active;
CREATE INDEX idx_usuarios_rol_id ON usuarios(rol_id);
CREATE INDEX idx_fichas_programa ON fichas(programa_id);
CREATE INDEX idx_asig_instructor_id ON asignaciones_instructor_ficha(instructor_id);
CREATE INDEX idx_coordinadores_empresa_empresa ON coordinadores_empresa(empresa_id);
CREATE INDEX idx_evidencias_uploaded_by ON evidencias_archivos(uploaded_by);
CREATE INDEX idx_procesos_aprendiz ON procesos_etapa_productiva(aprendiz_id);
CREATE INDEX idx_procesos_ficha ON procesos_etapa_productiva(ficha_id);
CREATE INDEX idx_procesos_modalidad ON procesos_etapa_productiva(modalidad_id);
CREATE INDEX idx_procesos_empresa ON procesos_etapa_productiva(empresa_id);
CREATE INDEX idx_procesos_coordinador ON procesos_etapa_productiva(coordinador_empresa_id);
CREATE INDEX idx_procesos_instructor ON procesos_etapa_productiva(instructor_id);
CREATE INDEX idx_procesos_estado ON procesos_etapa_productiva(estado);
CREATE INDEX idx_procesos_estado_sofia ON procesos_etapa_productiva(estado_sofia);
CREATE INDEX idx_procesos_estado_fecha_fin ON procesos_etapa_productiva(estado, fecha_fin);
CREATE INDEX idx_novedades_proceso ON novedades_proceso(proceso_id);
CREATE INDEX idx_novedades_tipo ON novedades_proceso(tipo_novedad);
CREATE INDEX idx_checklist_proceso ON checklist_documentos_proceso(proceso_id);
CREATE INDEX idx_checklist_estado ON checklist_documentos_proceso(estado);
CREATE INDEX idx_medidas_proceso ON medidas_formativas_proceso(proceso_id);
CREATE INDEX idx_charlas_instructor ON charlas(instructor_id);
CREATE INDEX idx_asistencias_aprendiz ON asistencias_charlas(aprendiz_id);
CREATE INDEX idx_reuniones_instructor ON reuniones_seguimiento(instructor_id);
CREATE INDEX idx_reuniones_proceso ON reuniones_seguimiento(proceso_id);
CREATE INDEX idx_bitacoras_proceso ON bitacoras(proceso_id);
CREATE INDEX idx_bitacoras_estado ON bitacoras(estado);
CREATE INDEX idx_bitacoras_periodo ON bitacoras(periodo_reportado);
CREATE INDEX idx_bitacora_evid_archivo ON bitacora_evidencias(evidencia_archivo_id);
CREATE INDEX idx_notif_destinatario ON notificaciones_mensajes(destinatario_usuario_id);
CREATE INDEX idx_notif_estado_envio ON notificaciones_mensajes(estado_envio_email);

-- ============================================================
-- 12. TRIGGERS DE AUDITORÍA (updated_at)
-- ============================================================
CREATE TRIGGER trg_roles_updated_at BEFORE UPDATE ON roles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_usuarios_updated_at BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_usuario_roles_updated_at BEFORE UPDATE ON usuario_roles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_programas_updated_at BEFORE UPDATE ON programas_formacion FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_fichas_updated_at BEFORE UPDATE ON fichas FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_asig_updated_at BEFORE UPDATE ON asignaciones_instructor_ficha FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_modalidades_updated_at BEFORE UPDATE ON modalidades_ep FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_empresas_updated_at BEFORE UPDATE ON empresas FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_coordinadores_updated_at BEFORE UPDATE ON coordinadores_empresa FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_evidencias_updated_at BEFORE UPDATE ON evidencias_archivos FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_procesos_updated_at BEFORE UPDATE ON procesos_etapa_productiva FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_charlas_updated_at BEFORE UPDATE ON charlas FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_asistencias_updated_at BEFORE UPDATE ON asistencias_charlas FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_reuniones_updated_at BEFORE UPDATE ON reuniones_seguimiento FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_bitacoras_updated_at BEFORE UPDATE ON bitacoras FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_bitacora_evid_updated_at BEFORE UPDATE ON bitacora_evidencias FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_novedades_updated_at BEFORE UPDATE ON novedades_proceso FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_notificaciones_updated_at BEFORE UPDATE ON notificaciones_mensajes FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_checklist_updated_at BEFORE UPDATE ON checklist_documentos_proceso FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_medidas_updated_at BEFORE UPDATE ON medidas_formativas_proceso FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- COMENTARIOS ADICIONALES
-- ============================================================
COMMENT ON COLUMN usuarios.rol_id IS 'Rol principal del usuario. Los roles adicionales se gestionan en usuario_roles.';
COMMENT ON COLUMN usuarios.tipo_documento IS 'Tipo de documento de identidad (TI, CC, CE, PTE).';
COMMENT ON COLUMN procesos_etapa_productiva.estado_sofia IS 'Control del estado del proceso en la plataforma SOFIA Plus.';
COMMENT ON COLUMN procesos_etapa_productiva.nota_empresa IS 'Nota de evaluación final asignada por la empresa (0-10).';
COMMENT ON COLUMN procesos_etapa_productiva.nota_instructor IS 'Nota de evaluación final asignada por el instructor (0-10).';
COMMENT ON TABLE novedades_proceso IS 'Registro de novedades durante la etapa productiva (renuncias, incapacidades, prórrogas, etc.).';
COMMENT ON TABLE checklist_documentos_proceso IS 'Checklist de documentos requeridos para el proceso de etapa productiva.';
COMMENT ON TABLE medidas_formativas_proceso IS 'Medidas formativas y alertas de deserción aplicadas al proceso.';
COMMENT ON COLUMN reuniones_seguimiento.archivo_f023_url IS 'URL directa al documento del Formato F023 (evidencia física).';
COMMENT ON COLUMN bitacoras.archivo_f147_url IS 'URL directa al documento del Formato F147 (bitácora).';

-- ============================================================
-- 13. DATOS SEMILLA (SEED)
-- ============================================================

-- 🔹 Roles
INSERT INTO roles (nombre, descripcion) VALUES
('Administrador', 'Acceso total al sistema'),
('Coordinador', 'Gestiona fichas, charlas y asignaciones'),
('Instructor', 'Realiza seguimiento y evalúa bitácoras'),
('Aprendiz', 'Registra bitácoras y evidencia de etapa productiva'),
('Apoyo Administrativo', 'Soporte operativo sin permisos de aprobación'),
('Consulta', 'Acceso de solo lectura')
ON CONFLICT (nombre) DO NOTHING;

-- 🔹 Modalidades
INSERT INTO modalidades_ep (nombre) VALUES
('Monitoria'),
('Vínculo laboral'),
('Vínculo formativo'),
('Contrato de aprendizaje'),
('Proyecto productivo'),
('Economía popular')
ON CONFLICT (nombre) DO NOTHING;

-- ============================================================
-- 🔥 USUARIOS DE PRUEBA
-- Contraseña para TODOS: Test1234
-- Hash bcrypt real: $2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i
-- ============================================================
INSERT INTO usuarios (nombre, apellido, email, password_hash, rol_id, is_active)
VALUES
    ('Admin',       'Sistema',  'usuario1@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 1, TRUE),
    ('Carlos',      'Ramírez',  'usuario2@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 3, TRUE),
    ('Pedro',       'Gómez',    'usuario3@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 4, TRUE),
    ('Laura',       'Martínez', 'usuario4@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 2, TRUE),
    ('Andrés',      'Pérez',    'usuario5@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 6, TRUE)
ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- 14. VERIFICACIÓN FINAL (te muestra lo que quedó)
-- ============================================================
SELECT 'Roles insertados' AS check_name, COUNT(*)::TEXT AS resultado FROM roles
UNION ALL
SELECT 'Modalidades insertadas', COUNT(*)::TEXT FROM modalidades_ep
UNION ALL
SELECT 'Usuarios insertados', COUNT(*)::TEXT FROM usuarios;

-- Detalle de usuarios con su rol
SELECT u.id, u.email, r.nombre AS rol, u.is_active,
       LEFT(u.password_hash, 30) || '...' AS hash_inicio
FROM usuarios u
JOIN roles r ON r.id = u.rol_id
ORDER BY u.id;