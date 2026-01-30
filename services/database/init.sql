-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de fuentes oficiales
CREATE TABLE sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(255) NOT NULL,
    base_url TEXT NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (
        type IN ('sismo', 'lluvia', 'corte')
    ),
    domain VARCHAR(255) NOT NULL,
    parser_config JSONB NOT NULL,
    frequency_sec INTEGER NOT NULL DEFAULT 300,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de eventos crudos (raw)
CREATE TABLE raw_events (
    raw_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    source_id UUID REFERENCES sources (source_id),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB NOT NULL,
    raw_hash VARCHAR(64) UNIQUE NOT NULL
);

-- Tabla de eventos normalizados
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
    status VARCHAR(50) DEFAULT 'NO_VERIFICADO' CHECK (
        status IN (
            'CONFIRMADO',
            'EN_VERIFICACION',
            'NO_VERIFICADO'
        )
    ),
    score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de reglas de verificación
CREATE TABLE verification_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(255) NOT NULL,
    weight INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT true
);

-- Tabla de usuarios
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (
        role IN ('admin', 'operator', 'user')
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de suscripciones
CREATE TABLE subscriptions (
    sub_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    user_id UUID REFERENCES users (user_id),
    type VARCHAR(50),
    zone VARCHAR(255),
    channel VARCHAR(50) NOT NULL CHECK (
        channel IN (
            'telegram',
            'email',
            'whatsapp'
        )
    ),
    channel_id VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de notificaciones
CREATE TABLE notifications (
    notif_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    event_id UUID REFERENCES events (event_id),
    sub_id UUID REFERENCES subscriptions (sub_id),
    channel VARCHAR(50) NOT NULL,
    to_address VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending' CHECK (
        status IN ('pending', 'sent', 'failed')
    ),
    error_message TEXT
);

-- Tabla de auditoría
CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    user_id UUID REFERENCES users (user_id),
    action VARCHAR(255) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Índices para optimización
CREATE INDEX idx_events_status ON events (status);

CREATE INDEX idx_events_type ON events(type);

CREATE INDEX idx_events_occurred_at ON events (occurred_at);

CREATE INDEX idx_events_zone ON events (zone);

CREATE INDEX idx_raw_events_source ON raw_events (source_id);

CREATE INDEX idx_subscriptions_user ON subscriptions (user_id);

CREATE INDEX idx_notifications_event ON notifications (event_id);

-- Insertar reglas de verificación por defecto
INSERT INTO
    verification_rules (name, weight, enabled)
VALUES (
        'Dominio en lista blanca',
        40,
        true
    ),
    (
        'Evidencia URL válida',
        15,
        true
    ),
    (
        'Timestamp reciente',
        15,
        true
    ),
    ('Campos completos', 10, true),
    (
        'Corroboración cruzada',
        20,
        true
    );

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar usuario admin por defecto (password: admin123)
INSERT INTO
    users (email, password_hash, role)
VALUES (
        'admin@sacv.local',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS8qB.W96',
        'admin'
    );

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Base de datos inicializada correctamente';
    RAISE NOTICE 'Usuario admin creado: admin@sacv.local / admin123';
END $$;