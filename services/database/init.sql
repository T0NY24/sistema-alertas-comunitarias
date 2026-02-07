-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

---
-- 1. TABLAS DE CATÁLOGO (PROVINCIAS Y UBICACIONES)
---
CREATE TABLE provinces (
    province_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE locations (
    location_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT true
);

---
-- 2. GESTIÓN DE USUARIOS
---
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

---
-- 3. FUENTES Y EVENTOS CRUDOS
---
CREATE TABLE sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(255) NOT NULL,
    base_url TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    parser_config JSONB NOT NULL,
    frequency_sec INTEGER DEFAULT 300,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE raw_events (
    raw_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    source_id UUID REFERENCES sources (source_id),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB NOT NULL,
    raw_hash VARCHAR(64) UNIQUE NOT NULL
);

---
-- 4. EVENTOS NORMALIZADOS
---
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    type VARCHAR(50) NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    zone VARCHAR(255),
    severity VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    evidence_url TEXT,
    source_id UUID REFERENCES sources (source_id),
    dedup_hash VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'NO_VERIFICADO',
    score INTEGER DEFAULT 0,
    province_id INTEGER REFERENCES provinces (province_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

---
-- 5. SUSCRIPCIONES Y NOTIFICACIONES
---
CREATE TABLE subscriptions (
    sub_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    user_id UUID REFERENCES users (user_id),
    type VARCHAR(50),
    zone VARCHAR(255),
    channel VARCHAR(50) NOT NULL,
    channel_id VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    province_id INTEGER REFERENCES provinces (province_id)
);

CREATE TABLE notifications (
    notif_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    event_id UUID REFERENCES events (event_id),
    sub_id UUID REFERENCES subscriptions (sub_id),
    channel VARCHAR(50) NOT NULL,
    to_address VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT
);

---
-- 6. AUDITORÍA Y REGLAS
---
CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    user_id UUID REFERENCES users (user_id),
    action VARCHAR(255) NOT NULL,
    entity VARCHAR(255) NOT NULL,
    entity_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE verification_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(255) NOT NULL,
    weight INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT true
);