/**
 * TypeScript types derived from PostgreSQL database schema (init.sql)
 * Sistema de Alertas Comunitarias Verificadas (SACV)
 */

// ====================================================================
// 1. CATÁLOGO (PROVINCIAS Y UBICACIONES)
// ====================================================================

export interface Province {
    province_id: number;
    name: string;
}

export interface Location {
    location_id: string;
    name: string;
    active: boolean;
}

// ====================================================================
// 2. GESTIÓN DE USUARIOS
// ====================================================================

export type UserRole = 'admin' | 'operator' | 'user';

export interface User {
    user_id: string;
    email: string;
    password_hash: string;
    role: UserRole;
    created_at: string;
}

// ====================================================================
// 3. FUENTES Y EVENTOS CRUDOS
// ====================================================================

export type SourceType = 'sismo' | 'lluvia' | 'corte';

export interface Source {
    source_id: string;
    name: string;
    base_url: string;
    type: string; // Changed from enum to string for flexibility
    domain: string;
    parser_config: Record<string, any>; // JSONB
    frequency_sec: number;
    active: boolean;
    created_at: string;
    updated_at: string;
}

export interface RawEvent {
    raw_id: string;
    source_id: string;
    fetched_at: string;
    raw_payload: Record<string, any>; // JSONB
    raw_hash: string;
}

// ====================================================================
// 4. EVENTOS NORMALIZADOS
// ====================================================================

export type EventStatus = 'CONFIRMADO' | 'EN_VERIFICACION' | 'NO_VERIFICADO';
export type EventSeverity = 'Alta' | 'Media' | 'Baja';

export interface Event {
    event_id: string;
    type: string;
    occurred_at: string;
    zone: string | null;
    severity: string | null;
    title: string;
    description: string | null;
    evidence_url: string | null;
    source_id: string | null;
    dedup_hash: string;
    status: string; // Changed from enum to string
    score: number;
    created_at: string;
    updated_at: string;
}

// ====================================================================
// 5. SUSCRIPCIONES Y NOTIFICACIONES
// ====================================================================

export type NotificationChannel = 'telegram' | 'email' | 'whatsapp';
export type NotificationStatus = 'pending' | 'sent' | 'failed';

export interface Subscription {
    sub_id: string;
    user_id: string;
    type: string | null;
    zone: string | null;
    channel: string; // Changed from enum to string
    channel_id: string;
    active: boolean;
    created_at: string;
    province_id: number | null;
}

export interface Notification {
    notif_id: string;
    event_id: string;
    sub_id: string;
    channel: string; // Changed from enum to string
    to_address: string;
    sent_at: string;
    status: string; // Changed from enum to string
    error_message: string | null;
}

// ====================================================================
// 6. AUDITORÍA Y REGLAS
// ====================================================================

export interface AuditLog {
    audit_id: string;
    user_id: string;
    action: string;
    entity: string;
    entity_id: string | null;
    timestamp: string;
    metadata: Record<string, any> | null; // JSONB
}

export interface VerificationRule {
    rule_id: string;
    name: string;
    weight: number;
    enabled: boolean;
}

// ====================================================================
// API RESPONSE TYPES
// ====================================================================

export interface ApiEventResponse {
    event_id: string;
    type: string;
    occurred_at: string;
    zone: string | null;
    severity: string | null;
    title: string;
    description: string | null;
    evidence_url: string | null;
    status: string;
    score: number;
    created_at: string;
}

export interface ApiStatsResponse {
    total_sources: number;
    active_sources: number;
    total_raw_events: number;
    total_events: number;
    events_by_status: {
        confirmados: number;
        en_verificacion: number;
        no_verificados: number;
    };
    last_scraping: string | null;
}

// ====================================================================
// FILTER TYPES
// ====================================================================

export interface EventFilters {
    type?: string;
    zone?: string;
    status?: EventStatus | '';
    severity?: EventSeverity | '';
    search?: string;
    page?: number;
    limit?: number;
    offset?: number;
}

