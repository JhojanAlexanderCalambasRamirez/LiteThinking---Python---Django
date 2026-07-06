-- =============================================================================
-- LiteThinking 2026 - Initial Schema
-- PostgreSQL 15+ | pgvector extension required
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for AI embeddings

-- =============================================================================
-- TYPES
-- =============================================================================

CREATE TYPE user_role AS ENUM ('admin', 'externo');
CREATE TYPE audit_action AS ENUM ('CREATE', 'UPDATE', 'DELETE');

-- =============================================================================
-- EMPRESA
-- =============================================================================

CREATE TABLE empresa (
    nit             VARCHAR(20)  PRIMARY KEY,
    nombre          VARCHAR(255) NOT NULL,
    direccion       TEXT         NOT NULL,
    telefono        VARCHAR(20)  NOT NULL,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- NIT colombiano: dígitos + guión opcional + dígito verificador
    -- Ej: 900123456-7 o 9001234567
    CONSTRAINT chk_empresa_nit_format
        CHECK (nit ~ '^\d{6,10}(-\d)?$'),

    CONSTRAINT chk_empresa_telefono_format
        CHECK (telefono ~ '^\+?[\d\s\-\(\)]{7,20}$')
);

COMMENT ON COLUMN empresa.nit IS 'NIT colombiano. Formato: XXXXXXXXX-X. PK natural de negocio.';
COMMENT ON COLUMN empresa.activo IS 'Soft delete. FALSE = empresa desactivada, no eliminada.';

-- =============================================================================
-- USUARIO
-- =============================================================================

CREATE TABLE usuario (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    nombre          VARCHAR(100),
    apellido        VARCHAR(100),
    rol             user_role    NOT NULL DEFAULT 'externo',
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_usuario_email UNIQUE (email),

    CONSTRAINT chk_usuario_email_format
        CHECK (email ~ '^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$'),

    -- bcrypt hash starts with $2b$ or $2a$; argon2 starts with $argon2
    CONSTRAINT chk_password_hash_not_plaintext
        CHECK (
            password_hash LIKE '$2b$%'
            OR password_hash LIKE '$2a$%'
            OR password_hash LIKE '$argon2%'
        )
);

COMMENT ON COLUMN usuario.password_hash IS 'Siempre almacenar hash (bcrypt/argon2). Nunca texto plano.';
COMMENT ON COLUMN usuario.rol IS 'admin: CRUD completo. externo: solo lectura empresa.';

-- =============================================================================
-- REFRESH TOKENS (JWT invalidation support)
-- =============================================================================

CREATE TABLE refresh_token (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id      UUID         NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    token_hash      VARCHAR(64)  NOT NULL,   -- SHA256 del token real
    expires_at      TIMESTAMPTZ  NOT NULL,
    revoked         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_refresh_token_hash UNIQUE (token_hash)
);

COMMENT ON TABLE refresh_token IS 'Permite invalidar JWT refresh tokens (logout, cambio de contraseña).';
COMMENT ON COLUMN refresh_token.token_hash IS 'SHA256 del token. Nunca almacenar token en claro.';

CREATE INDEX idx_refresh_token_usuario ON refresh_token(usuario_id);
CREATE INDEX idx_refresh_token_expires ON refresh_token(expires_at) WHERE revoked = FALSE;

-- =============================================================================
-- MONEDA (catálogo ISO 4217)
-- =============================================================================

CREATE TABLE moneda (
    codigo          VARCHAR(3)   PRIMARY KEY,   -- ISO 4217: USD, COP, EUR
    nombre          VARCHAR(50)  NOT NULL,
    simbolo         VARCHAR(5)   NOT NULL,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_moneda_codigo_upper
        CHECK (codigo = UPPER(codigo))
);

COMMENT ON COLUMN moneda.codigo IS 'ISO 4217. Siempre uppercase. Ej: USD, COP, EUR, GBP.';

-- =============================================================================
-- PRODUCTO
-- =============================================================================

CREATE TABLE producto (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo          VARCHAR(50)  NOT NULL,
    nombre          VARCHAR(255) NOT NULL,
    caracteristicas TEXT,
    empresa_nit     VARCHAR(20)  NOT NULL
                        REFERENCES empresa(nit)
                        ON DELETE RESTRICT
                        ON UPDATE CASCADE,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Código único POR empresa (misma empresa no puede tener dos productos con mismo código)
    CONSTRAINT uq_producto_codigo_empresa UNIQUE (codigo, empresa_nit)
);

COMMENT ON CONSTRAINT uq_producto_codigo_empresa ON producto
    IS 'Código único por empresa. Distintas empresas pueden reusar el mismo código.';
COMMENT ON COLUMN producto.empresa_nit IS 'RESTRICT: no se puede eliminar empresa si tiene productos.';

-- =============================================================================
-- PRODUCTO PRECIO (multi-moneda - 1NF normalizado)
-- =============================================================================

CREATE TABLE producto_precio (
    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id     UUID          NOT NULL
                        REFERENCES producto(id)
                        ON DELETE CASCADE,
    moneda_codigo   VARCHAR(3)    NOT NULL
                        REFERENCES moneda(codigo)
                        ON DELETE RESTRICT,
    precio          NUMERIC(18,4) NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- Un precio por moneda por producto
    CONSTRAINT uq_producto_precio_moneda UNIQUE (producto_id, moneda_codigo),

    -- Precio no puede ser negativo. 0 permitido (producto gratuito/sin precio definido)
    CONSTRAINT chk_precio_no_negativo CHECK (precio >= 0)
);

COMMENT ON TABLE producto_precio IS 'Precios en múltiples monedas. Normalizado: no JSONB, no columnas separadas.';
COMMENT ON COLUMN producto_precio.precio IS 'NUMERIC(18,4): nunca FLOAT para valores monetarios.';

-- =============================================================================
-- INVENTARIO
-- =============================================================================

CREATE TABLE inventario (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id     UUID         NOT NULL
                        REFERENCES producto(id)
                        ON DELETE RESTRICT,
    cantidad        INTEGER      NOT NULL DEFAULT 1,
    observaciones   TEXT,
    created_by      UUID
                        REFERENCES usuario(id)
                        ON DELETE SET NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Un registro de inventario por producto
    CONSTRAINT uq_inventario_producto UNIQUE (producto_id),

    -- Stock nunca negativo
    CONSTRAINT chk_inventario_cantidad_no_negativa CHECK (cantidad >= 0)
);

COMMENT ON TABLE inventario IS 'Stock por producto. empresa se obtiene via JOIN inventario→producto→empresa.';
COMMENT ON COLUMN inventario.created_by IS 'Solo admins pueden crear entradas. SET NULL si usuario se desactiva.';
COMMENT ON COLUMN inventario.cantidad IS 'CHECK >= 0: stock no puede ser negativo.';

-- =============================================================================
-- BLOCKCHAIN AUDIT LOG
-- =============================================================================

CREATE TABLE blockchain_log (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(50)  NOT NULL,     -- 'inventario' | 'empresa' | 'producto'
    entity_id       VARCHAR(255) NOT NULL,     -- UUID o NIT del registro afectado
    accion          audit_action NOT NULL,
    data_hash       VARCHAR(64)  NOT NULL,     -- SHA256 del payload en el momento del evento
    tx_hash         VARCHAR(66),               -- Hash tx Ethereum: 0x + 64 hex chars
    block_number    BIGINT,
    network         VARCHAR(50),               -- 'polygon-mumbai' | 'ethereum-sepolia'
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_tx_hash_format
        CHECK (tx_hash IS NULL OR tx_hash ~ '^0x[a-fA-F0-9]{64}$')
);

COMMENT ON TABLE blockchain_log IS 'Registro inmutable de operaciones críticas. tx_hash NULL si blockchain no disponible (async).';
COMMENT ON COLUMN blockchain_log.data_hash IS 'SHA256 del record serializado. Verificable sin blockchain.';

-- =============================================================================
-- AI EMBEDDINGS (pgvector)
-- =============================================================================

CREATE TABLE producto_embedding (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id     UUID         NOT NULL
                        REFERENCES producto(id)
                        ON DELETE CASCADE,
    embedding       vector(384),               -- sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    model_name      VARCHAR(100) NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Un embedding por modelo por producto
    CONSTRAINT uq_producto_embedding_model UNIQUE (producto_id, model_name)
);

COMMENT ON TABLE producto_embedding IS 'Embeddings para búsqueda semántica. Dimensión 384 = sentence-transformers multilingual.';

-- IVFFlat index para búsqueda coseno eficiente
-- lists = sqrt(N_rows) es regla general. Ajustar según volumen real.
CREATE INDEX idx_producto_embedding_ivfflat
    ON producto_embedding
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- =============================================================================
-- EMAIL LOG (auditoría de envíos de PDF)
-- =============================================================================

CREATE TABLE email_log (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    destinatario    VARCHAR(255) NOT NULL,
    asunto          VARCHAR(255) NOT NULL,
    empresa_nit     VARCHAR(20)  REFERENCES empresa(nit) ON DELETE SET NULL,
    enviado_por     UUID         REFERENCES usuario(id) ON DELETE SET NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',  -- pending|sent|failed
    error_mensaje   TEXT,
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_email_log_status
        CHECK (status IN ('pending', 'sent', 'failed'))
);

COMMENT ON TABLE email_log IS 'Auditoría de PDFs enviados desde vista Inventario.';

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- empresa
CREATE INDEX idx_empresa_activo ON empresa(activo) WHERE activo = TRUE;
CREATE INDEX idx_empresa_nombre ON empresa(nombre);

-- usuario
CREATE INDEX idx_usuario_activo ON usuario(activo) WHERE activo = TRUE;
CREATE INDEX idx_usuario_rol ON usuario(rol);

-- producto
CREATE INDEX idx_producto_empresa ON producto(empresa_nit);
CREATE INDEX idx_producto_activo ON producto(activo) WHERE activo = TRUE;
CREATE INDEX idx_producto_nombre ON producto(nombre);

-- producto_precio
CREATE INDEX idx_producto_precio_producto ON producto_precio(producto_id);

-- inventario
CREATE INDEX idx_inventario_created_by ON inventario(created_by);

-- blockchain_log
CREATE INDEX idx_blockchain_entity ON blockchain_log(entity_type, entity_id);
CREATE INDEX idx_blockchain_created ON blockchain_log(created_at DESC);

-- email_log
CREATE INDEX idx_email_log_empresa ON email_log(empresa_nit);
CREATE INDEX idx_email_log_status ON email_log(status) WHERE status = 'pending';

-- =============================================================================
-- AUTO-UPDATE updated_at TRIGGER
-- =============================================================================

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_empresa
    BEFORE UPDATE ON empresa
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_usuario
    BEFORE UPDATE ON usuario
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_producto
    BEFORE UPDATE ON producto
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_producto_precio
    BEFORE UPDATE ON producto_precio
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_inventario
    BEFORE UPDATE ON inventario
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_producto_embedding
    BEFORE UPDATE ON producto_embedding
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
