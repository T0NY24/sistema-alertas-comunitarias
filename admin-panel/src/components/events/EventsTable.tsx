import React, { useState } from 'react';
import { useEvents, useUpdateEventStatus } from '../../api/endpoints';
import type { EventFilters, EventStatus, EventSeverity } from '../../types/database';
import { Filter, Search, ChevronLeft, ChevronRight, Activity, CloudRain, Zap, CheckCircle, XCircle } from 'lucide-react';

export const EventsTable: React.FC = () => {
    const [filters, setFilters] = useState<EventFilters>({
        limit: 20,
        offset: 0,
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedStatus, setSelectedStatus] = useState<EventStatus | ''>('');
    const [selectedSeverity, setSelectedSeverity] = useState<EventSeverity | ''>('');

    const { data: events, isLoading, error } = useEvents(filters);
    const updateEventMutation = useUpdateEventStatus();

    const handleConfirm = (eventId: string) => {
        if (confirm('¿Confirmar este evento? Se enviará automáticamente por Telegram.')) {
            updateEventMutation.mutate(
                { eventId, status: 'CONFIRMADO' },
                {
                    onSuccess: () => {
                        alert('✅ Evento confirmado y publicado correctamente');
                    },
                    onError: (error: any) => {
                        alert(`❌ Error: ${error.message}`);
                    }
                }
            );
        }
    };

    const handleReject = (eventId: string) => {
        if (confirm('¿Rechazar este evento?')) {
            updateEventMutation.mutate(
                { eventId, status: 'NO_VERIFICADO' },
                {
                    onSuccess: () => {
                        alert('❌ Evento rechazado');
                    },
                    onError: (error: any) => {
                        alert(`❌ Error: ${error.message}`);
                    }
                }
            );
        }
    };

    // Filtrado local por búsqueda
    const filteredEvents = events?.filter(event => {
        const matchesSearch = searchTerm === '' ||
            event.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            event.description?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesStatus = !selectedStatus || event.status === selectedStatus;
        const matchesSeverity = !selectedSeverity || event.severity === selectedSeverity;

        return matchesSearch && matchesStatus && matchesSeverity;
    });

    const handlePrevPage = () => {
        setFilters(prev => ({
            ...prev,
            offset: Math.max(0, (prev.offset || 0) - (prev.limit || 20))
        }));
    };

    const handleNextPage = () => {
        setFilters(prev => ({
            ...prev,
            offset: (prev.offset || 0) + (prev.limit || 20)
        }));
    };

    const getStatusBadgeClass = (status: string) => {
        switch (status) {
            case 'CONFIRMADO':
                return 'badge-success';
            case 'EN_VERIFICACION':
                return 'badge-warning';
            case 'NO_VERIFICADO':
                return 'badge-info';
            default:
                return 'badge-info';
        }
    };

    const getSeverityBadgeClass = (severity: string | null) => {
        switch (severity) {
            case 'Alta':
                return 'badge-danger';
            case 'Media':
                return 'badge-warning';
            case 'Baja':
                return 'badge-info';
            default:
                return 'badge-info';
        }
    };

    const getEventIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'sismo':
                return <Activity className="w-4 h-4" />;
            case 'lluvia':
                return <CloudRain className="w-4 h-4" />;
            case 'corte':
                return <Zap className="w-4 h-4" />;
            default:
                return <Activity className="w-4 h-4" />;
        }
    };

    if (error) {
        return (
            <div className="card">
                <div className="text-red-400">
                    Error cargando eventos: {error instanceof Error ? error.message : 'Error desconocido'}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Header con filtros */}
            <div className="card">
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Filter className="w-6 h-6 text-midnight-accent" />
                        Eventos Normalizados
                    </h2>

                    {/* Búsqueda */}
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Buscar por título o descripción..."
                            className="input-field w-full pl-10"
                            aria-label="Buscar eventos por título o descripción"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                {/* Filtros de Status y Severity */}
                <div className="flex flex-wrap gap-4 mt-4">
                    <div>
                        <label htmlFor="status-filter" className="block text-sm font-medium text-gray-300 mb-2">Estado</label>
                        <select
                            id="status-filter"
                            className="input-field"
                            aria-label="Filtrar eventos por estado"
                            value={selectedStatus}
                            onChange={(e) => setSelectedStatus(e.target.value as EventStatus | '')}
                        >
                            <option value="">Todos</option>
                            <option value="CONFIRMADO">Confirmado</option>
                            <option value="EN_VERIFICACION">En Verificación</option>
                            <option value="NO_VERIFICADO">No Verificado</option>
                        </select>
                    </div>

                    <div>
                        <label htmlFor="severity-filter" className="block text-sm font-medium text-gray-300 mb-2">Severidad</label>
                        <select
                            id="severity-filter"
                            className="input-field"
                            aria-label="Filtrar eventos por severidad"
                            value={selectedSeverity}
                            onChange={(e) => setSelectedSeverity(e.target.value as EventSeverity | '')}
                        >
                            <option value="">Todas</option>
                            <option value="Alta">Alta</option>
                            <option value="Media">Media</option>
                            <option value="Baja">Baja</option>
                        </select>
                    </div>

                    {selectedStatus || selectedSeverity || searchTerm ? (
                        <button
                            onClick={() => {
                                setSelectedStatus('');
                                setSelectedSeverity('');
                                setSearchTerm('');
                            }}
                            className="btn-secondary self-end"
                        >
                            Limpiar Filtros
                        </button>
                    ) : null}
                </div>
            </div>

            {/* Tabla */}
            <div className="card overflow-hidden">
                {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-midnight-accent"></div>
                    </div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-midnight-border">
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Tipo</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Título</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Zona</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Severidad</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Estado</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Score</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Fecha</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-midnight-border">
                                    {filteredEvents?.map((event) => (
                                        <tr
                                            key={event.event_id}
                                            className="hover:bg-midnight-bg/50 transition-colors cursor-pointer"
                                        >
                                            <td className="px-4 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-midnight-accent">
                                                        {getEventIcon(event.type)}
                                                    </span>
                                                    <span className="text-sm font-medium capitalize">{event.type}</span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-4">
                                                <div className="text-sm font-medium text-white max-w-xs truncate">
                                                    {event.title}
                                                </div>
                                                {event.description && (
                                                    <div className="text-xs text-gray-400 max-w-xs truncate mt-1">
                                                        {event.description}
                                                    </div>
                                                )}
                                            </td>
                                            <td className="px-4 py-4 whitespace-nowrap">
                                                <span className="text-sm text-gray-300">{event.zone || '-'}</span>
                                            </td>
                                            <td className="px-4 py-4 whitespace-nowrap">
                                                {event.severity ? (
                                                    <span className={getSeverityBadgeClass(event.severity)}>
                                                        {event.severity}
                                                    </span>
                                                ) : (
                                                    <span className="text-gray-500">-</span>
                                                )}
                                            </td>
                                            <td className="px-4 py-4 whitespace-nowrap">
                                                <span className={getStatusBadgeClass(event.status)}>
                                                    {event.status.replace('_', ' ')}
                                                </span>
                                            </td>
                                            <td className="px-4 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-16 bg-gray-700 rounded-full h-2 overflow-hidden">
                                                        <div
                                                            className="bg-midnight-accent h-2 rounded-full transition-all"
                                                            style={{ width: `${Math.min(100, event.score)}%` }}
                                                            role="progressbar"
                                                            aria-valuenow={event.score}
                                                            aria-valuemin={0}
                                                            aria-valuemax={100}
                                                            aria-label={`Score de confianza: ${event.score}%`}
                                                        />
                                                    </div>
                                                    <span className="text-xs text-gray-400">{event.score}</span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-400">
                                                {new Date(event.occurred_at).toLocaleString('es-ES', {
                                                    year: 'numeric',
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </td>
                                            <td className="px-4 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => handleConfirm(event.event_id)}
                                                        disabled={updateEventMutation.isPending || event.status === 'CONFIRMADO'}
                                                        className="inline-flex items-center gap-1 px-3 py-1 rounded bg-green-500/20 text-green-400 border border-green-500/30 text-xs font-semibold hover:bg-green-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                                        title={event.status === 'CONFIRMADO' ? 'Ya confirmado' : 'Confirmar evento'}
                                                    >
                                                        <CheckCircle className="w-3 h-3" />
                                                        Confirmar
                                                    </button>
                                                    <button
                                                        onClick={() => handleReject(event.event_id)}
                                                        disabled={updateEventMutation.isPending || event.status === 'NO_VERIFICADO'}
                                                        className="inline-flex items-center gap-1 px-3 py-1 rounded bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-semibold hover:bg-red-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                                        title={event.status === 'NO_VERIFICADO' ? 'Ya rechazado' : 'Rechazar evento'}
                                                    >
                                                        <XCircle className="w-3 h-3" />
                                                        Rechazar
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Paginación */}
                        <div className="flex items-center justify-between px-4 py-3 border-t border-midnight-border">
                            <div className="text-sm text-gray-400">
                                Mostrando {filteredEvents?.length || 0} eventos
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={handlePrevPage}
                                    disabled={!filters.offset || filters.offset === 0}
                                    className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                    Anterior
                                </button>
                                <button
                                    onClick={handleNextPage}
                                    disabled={!events || events.length < (filters.limit || 20)}
                                    className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                                >
                                    Siguiente
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
