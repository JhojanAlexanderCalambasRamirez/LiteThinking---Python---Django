-- =============================================================================
-- LiteThinking 2026 - Seed Data
-- Monedas ISO 4217 + usuario admin inicial
-- =============================================================================

-- Monedas base (ISO 4217)
INSERT INTO moneda (codigo, nombre, simbolo) VALUES
    ('COP', 'Peso Colombiano',    '$'),
    ('USD', 'Dólar Estadounidense', '$'),
    ('EUR', 'Euro',                '€'),
    ('GBP', 'Libra Esterlina',    '£'),
    ('BRL', 'Real Brasileño',     'R$'),
    ('MXN', 'Peso Mexicano',      '$')
ON CONFLICT (codigo) DO NOTHING;

-- =============================================================================
-- NOTA: el usuario admin se crea vía API/aplicación, NO hardcodeado aquí.
-- La contraseña DEBE ser hasheada por la aplicación (bcrypt/argon2).
-- Este seed solo existe como referencia del formato esperado.
-- =============================================================================

-- Empresa de ejemplo (desarrollo local)
INSERT INTO empresa (nit, nombre, direccion, telefono) VALUES
    ('900123456-7', 'LiteThinking S.A.S.', 'Cra 7 # 32-16, Bogotá', '+57 601 234 5678')
ON CONFLICT (nit) DO NOTHING;
