-- ============================================================
-- SCRIPT COMPLETO - SIPA (Actualizado con todos los cambios)
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
-- 2. FUNCIÓN DE AUDITORÍA
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 3. TABLAS BASE
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
    reset_code VARCHAR(6),
    reset_code_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_usuarios_rol FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE RESTRICT,
    CONSTRAINT ck_usuarios_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

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

-- 🔥 TABLA FICHAS CON LAS COLUMNAS NUEVAS
CREATE TABLE fichas (
    id BIGSERIAL PRIMARY KEY,
    programa_id BIGINT NOT NULL,
    numero_ficha VARCHAR(20) NOT NULL UNIQUE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    nivel VARCHAR(50) DEFAULT 'Tecnólogo',
    jornada VARCHAR(50) DEFAULT 'Mañana',
    aprendices_esperados INTEGER DEFAULT 0,
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
-- 4. EMPRESAS Y MODALIDADES
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

-- 🔥 TABLA EMPRESAS CON COLUMNA ARL NUEVA
CREATE TABLE empresas (
    id BIGSERIAL PRIMARY KEY,
    nit VARCHAR(20) NOT NULL UNIQUE,
    razon_social VARCHAR(200) NOT NULL,
    direccion VARCHAR(200),
    telefono VARCHAR(20),
    correo_contacto VARCHAR(150),
    arl VARCHAR(100),
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
-- 5. EVIDENCIAS
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
-- 6. PROCESOS
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
-- 7. SEGUIMIENTO
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
    CONSTRAINT ck_reunion_fechas CHECK (fecha_realizada IS NULL OR fecha_realizada >= fecha_programada)
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
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT fk_novedad_proceso FOREIGN KEY (proceso_id) REFERENCES procesos_etapa_productiva(id) ON DELETE CASCADE
);

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
    CONSTRAINT uq_medidas_proceso UNIQUE (proceso_id)
);

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
    CONSTRAINT uq_asistencia_charla_aprendiz UNIQUE (charla_id, aprendiz_id)
);

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
-- 8. ÍNDICES
-- ============================================================
CREATE INDEX idx_usuario_roles_rol ON usuario_roles(rol_id);
CREATE INDEX idx_usuarios_email_active ON usuarios(email) WHERE is_active;
CREATE INDEX idx_usuarios_rol_id ON usuarios(rol_id);
CREATE INDEX idx_usuarios_reset_code ON usuarios(reset_code) WHERE reset_code IS NOT NULL;
CREATE INDEX idx_fichas_programa ON fichas(programa_id);
CREATE INDEX idx_asig_instructor_id ON asignaciones_instructor_ficha(instructor_id);
CREATE INDEX idx_coordinadores_empresa_empresa ON coordinadores_empresa(empresa_id);
CREATE INDEX idx_evidencias_uploaded_by ON evidencias_archivos(uploaded_by);
CREATE INDEX idx_procesos_aprendiz ON procesos_etapa_productiva(aprendiz_id);
CREATE INDEX idx_procesos_ficha ON procesos_etapa_productiva(ficha_id);
CREATE INDEX idx_procesos_modalidad ON procesos_etapa_productiva(modalidad_id);
CREATE INDEX idx_procesos_empresa ON procesos_etapa_productiva(empresa_id);
CREATE INDEX idx_procesos_instructor ON procesos_etapa_productiva(instructor_id);
CREATE INDEX idx_procesos_estado ON procesos_etapa_productiva(estado);
CREATE INDEX idx_novedades_proceso ON novedades_proceso(proceso_id);
CREATE INDEX idx_checklist_proceso ON checklist_documentos_proceso(proceso_id);
CREATE INDEX idx_medidas_proceso ON medidas_formativas_proceso(proceso_id);
CREATE INDEX idx_charlas_instructor ON charlas(instructor_id);
CREATE INDEX idx_asistencias_aprendiz ON asistencias_charlas(aprendiz_id);
CREATE INDEX idx_reuniones_instructor ON reuniones_seguimiento(instructor_id);
CREATE INDEX idx_reuniones_proceso ON reuniones_seguimiento(proceso_id);
CREATE INDEX idx_bitacoras_proceso ON bitacoras(proceso_id);
CREATE INDEX idx_bitacoras_estado ON bitacoras(estado);
CREATE INDEX idx_bitacora_evid_archivo ON bitacora_evidencias(evidencia_archivo_id);
CREATE INDEX idx_notif_destinatario ON notificaciones_mensajes(destinatario_usuario_id);
CREATE INDEX idx_notif_estado_envio ON notificaciones_mensajes(estado_envio_email);

-- ============================================================
-- 9. TRIGGERS DE AUDITORÍA
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
-- 10. DATOS SEMILLA
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

-- 🔹 Programas de formación
INSERT INTO programas_formacion (codigo, nombre, descripcion) VALUES
('228106', 'Análisis y Desarrollo de Software', 'Programa tecnólogo en desarrollo de software'),
('122112', 'Gestión Empresarial', 'Programa tecnólogo en gestión empresarial'),
('133100', 'Contabilidad y Finanzas', 'Programa técnico en contabilidad'),
('228118', 'Desarrollo Web', 'Programa tecnólogo en desarrollo web')
ON CONFLICT (codigo) DO NOTHING;

-- 🔹 Usuarios de prueba (contraseña: Test1234)
INSERT INTO usuarios (nombre, apellido, email, password_hash, rol_id, is_active)
VALUES
    ('Admin',   'Sistema',  'usuario1@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 1, TRUE),
    ('Carlos',  'Ramírez',  'usuario2@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 3, TRUE),
    ('Pedro',   'Gómez',    'usuario3@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 4, TRUE),
    ('Laura',   'Martínez', 'usuario4@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 2, TRUE),
    ('Andrés',  'Pérez',    'usuario5@test.com', '$2b$12$29YhmtZimHMsmWtc8oWtJeFgik/258Txyc8v6xytmSYXIC4Tudx0i', 6, TRUE)
ON CONFLICT (email) DO NOTHING;

-- 🔹 Fichas de prueba
INSERT INTO fichas (programa_id, numero_ficha, fecha_inicio, fecha_fin, nivel, jornada, aprendices_esperados)
VALUES
    (1, '2875901', '2025-01-15', '2025-12-15', 'Tecnólogo', 'Mañana', 28),
    (2, '2875902', '2025-01-20', '2025-12-20', 'Tecnólogo', 'Tarde', 24),
    (3, '2875903', '2025-02-10', '2025-11-10', 'Técnico', 'Noche', 32),
    (4, '2875904', '2025-03-01', '2025-12-01', 'Tecnólogo', 'Mañana', 20)
ON CONFLICT (numero_ficha) DO NOTHING;

-- 🔹 Empresas de prueba (con ARL)
INSERT INTO empresas (nit, razon_social, direccion, telefono, correo_contacto, arl) VALUES
    ('900123456-1', 'TechSoft S.A.S.', 'Calle 123 #45-67', '3001234567', 'contacto@techsoft.com', 'SURA'),
    ('900987654-2', 'Innovar Solutions', 'Carrera 89 #12-34', '3109876543', 'info@innovar.com', 'Positiva'),
    ('900555444-3', 'SENA - Centro de Formación', 'Calle 100 #20-30', '3153334444', 'sena@sena.edu.co', 'Colpatria')
ON CONFLICT (nit) DO NOTHING;

-- 🔹 Coordinadores de empresa
INSERT INTO coordinadores_empresa (empresa_id, nombre, cargo, correo, telefono)
SELECT e.id, 'Ana Coordinadora', 'Jefe de Talento Humano', 'ana@techsoft.com', '3001234567'
FROM empresas e WHERE e.nit = '900123456-1'
ON CONFLICT DO NOTHING;

INSERT INTO coordinadores_empresa (empresa_id, nombre, cargo, correo, telefono)
SELECT e.id, 'Luis Coordinador', 'Gerente de RRHH', 'luis@innovar.com', '3109876543'
FROM empresas e WHERE e.nit = '900987654-2'
ON CONFLICT DO NOTHING;

-- 🔹 Procesos de etapa productiva (asignan aprendices a la ficha 2875901)
INSERT INTO procesos_etapa_productiva 
    (aprendiz_id, ficha_id, modalidad_id, empresa_id, coordinador_empresa_id, instructor_id, 
     fecha_inicio, fecha_fin, estado, estado_sofia, nota_empresa, nota_instructor)
SELECT 
    u.id, f.id, 1,
    e.id, c.id, 2,
    '2025-01-15', '2025-12-15', 'ACTIVO', 'PENDIENTE', NULL, NULL
FROM usuarios u, fichas f, empresas e, coordinadores_empresa c
WHERE u.email = 'usuario3@test.com'
  AND f.numero_ficha = '2875901'
  AND e.nit = '900123456-1'
  AND c.nombre = 'Ana Coordinadora'
ON CONFLICT DO NOTHING;

INSERT INTO procesos_etapa_productiva 
    (aprendiz_id, ficha_id, modalidad_id, empresa_id, coordinador_empresa_id, instructor_id, 
     fecha_inicio, fecha_fin, estado, estado_sofia)
SELECT 
    u.id, f.id, 2,
    e.id, c.id, 2,
    '2025-01-15', '2025-12-15', 'ACTIVO', 'PENDIENTE'
FROM usuarios u, fichas f, empresas e, coordinadores_empresa c
WHERE u.email = 'usuario5@test.com'
  AND f.numero_ficha = '2875901'
  AND e.nit = '900987654-2'
  AND c.nombre = 'Luis Coordinador'
ON CONFLICT DO NOTHING;

-- ============================================================
-- 11. VERIFICACIÓN FINAL
-- ============================================================
SELECT 'Roles' AS tabla, COUNT(*) AS total FROM roles
UNION ALL SELECT 'Modalidades', COUNT(*) FROM modalidades_ep
UNION ALL SELECT 'Programas', COUNT(*) FROM programas_formacion
UNION ALL SELECT 'Usuarios', COUNT(*) FROM usuarios
UNION ALL SELECT 'Fichas', COUNT(*) FROM fichas
UNION ALL SELECT 'Empresas', COUNT(*) FROM empresas
UNION ALL SELECT 'Coordinadores', COUNT(*) FROM coordinadores_empresa
UNION ALL SELECT 'Procesos', COUNT(*) FROM procesos_etapa_productiva
ORDER BY tabla;

-- Detalle de procesos (aprendices en la ficha 2875901)
SELECT 
    p.id,
    u.nombre || ' ' || u.apellido AS aprendiz,
    f.numero_ficha,
    e.razon_social AS empresa,
    e.arl,
    m.nombre AS modalidad,
    p.estado
FROM procesos_etapa_productiva p
JOIN usuarios u ON u.id = p.aprendiz_id
JOIN fichas f ON f.id = p.ficha_id
LEFT JOIN empresas e ON e.id = p.empresa_id
LEFT JOIN modalidades_ep m ON m.id = p.modalidad_id
ORDER BY p.id;