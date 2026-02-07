// Configuración centralizada del Admin Panel
// ESTE ARCHIVO SOBRESCRIBE CUALQUIER ENV VAR

export const CONFIG = {
    // API URL - HARDCODED para VPS
    API_BASE_URL: 'http://217.216.67.99:8001',

    // Timeouts
    API_TIMEOUT: 30000,

    // Refresh intervals
    STATS_REFRESH_INTERVAL: 30000,
    EVENTS_REFRESH_INTERVAL: 10000,
} as const;

// Export directo para compatibilidad
export const API_BASE_URL = CONFIG.API_BASE_URL;
