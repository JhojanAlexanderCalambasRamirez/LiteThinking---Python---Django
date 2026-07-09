-- =============================================================================
-- LiteThinking 2026 - Extra tables (not managed by Django ORM)
-- Run AFTER manage.py migrate
-- Requires: pgvector extension, tables empresa and producto (created by migrate)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ENUM used by blockchain_log
DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM ('CREATE', 'UPDATE', 'DELETE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- BLOCKCHAIN AUDIT LOG
-- =============================================================================

CREATE TABLE IF NOT EXISTS blockchain_log (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(50)  NOT NULL,
    entity_id       VARCHAR(255) NOT NULL,
    accion          audit_action NOT NULL,
    data_hash       VARCHAR(64)  NOT NULL,
    tx_hash         VARCHAR(66),
    block_number    BIGINT,
    network         VARCHAR(50),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_tx_hash_format
        CHECK (tx_hash IS NULL OR tx_hash ~ '^0x[a-fA-F0-9]{64}$')
);

CREATE INDEX IF NOT EXISTS idx_blockchain_entity ON blockchain_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_created ON blockchain_log(created_at DESC);

-- =============================================================================
-- AI EMBEDDINGS (pgvector)
-- =============================================================================

CREATE TABLE IF NOT EXISTS producto_embedding (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id     UUID         NOT NULL
                        REFERENCES producto(id)
                        ON DELETE CASCADE,
    embedding       vector(384),
    model_name      VARCHAR(100) NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_producto_embedding_model UNIQUE (producto_id, model_name)
);

CREATE INDEX IF NOT EXISTS idx_producto_embedding_ivfflat
    ON producto_embedding
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- =============================================================================
-- EMAIL LOG
-- =============================================================================

CREATE TABLE IF NOT EXISTS email_log (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    destinatario    VARCHAR(255) NOT NULL,
    asunto          VARCHAR(255) NOT NULL,
    empresa_nit     VARCHAR(20)  REFERENCES empresa(nit) ON DELETE SET NULL,
    enviado_por     UUID         REFERENCES usuario(id) ON DELETE SET NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
    error_mensaje   TEXT,
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_email_log_status
        CHECK (status IN ('pending', 'sent', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_email_log_empresa ON email_log(empresa_nit);
CREATE INDEX IF NOT EXISTS idx_email_log_status  ON email_log(status) WHERE status = 'pending';

-- =============================================================================
-- AUTO-UPDATE updated_at TRIGGER (for producto_embedding)
-- =============================================================================

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    CREATE TRIGGER set_updated_at_producto_embedding
        BEFORE UPDATE ON producto_embedding
        FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
