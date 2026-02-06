import React from 'react';
import { useStats } from '../../api/endpoints';
import { StatCard } from '../common/StatCard';
import { Activity, CheckCircle, Clock, AlertTriangle, Database, Wifi } from 'lucide-react';

export const Dashboard: React.FC = () => {
    const { data: stats, isLoading, error } = useStats();

    if (error) {
        return (
            <div className="card">
                <div className="text-red-400">
                    Error cargando estadísticas: {error instanceof Error ? error.message : 'Error desconocido'}
                </div>
            </div>
        );
    }

    // Calcular porcentajes para los badges
    const totalEvents = stats?.total_events || 0;
    const confirmados = stats?.events_by_status.confirmados || 0;
    const enVerificacion = stats?.events_by_status.en_verificacion || 0;
    const noVerificados = stats?.events_by_status.no_verificados || 0;

    const confirmedPercentage = totalEvents > 0 ? Math.round((confirmados / totalEvents) * 100) : 0;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-white">Dashboard de Operaciones</h2>
                <p className="text-sm text-gray-400 mt-1">
                    Monitoreo en tiempo real del sistema de alertas
                </p>
            </div>

            {/* KPI Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Total de Eventos */}
                <StatCard
                    title="Total de Eventos"
                    value={totalEvents}
                    icon={Activity}
                    color="blue"
                    loading={isLoading}
                />

                {/* Eventos Confirmados */}
                <StatCard
                    title="Eventos Confirmados"
                    value={confirmados}
                    icon={CheckCircle}
                    color="green"
                    loading={isLoading}
                    trend={{
                        value: confirmedPercentage,
                        isPositive: confirmedPercentage > 50
                    }}
                />

                {/* En Verificación */}
                <StatCard
                    title="En Verificación"
                    value={enVerificacion}
                    icon={Clock}
                    color="yellow"
                    loading={isLoading}
                />

                {/* No Verificados */}
                <StatCard
                    title="No Verificados"
                    value={noVerificados}
                    icon={AlertTriangle}
                    color="red"
                    loading={isLoading}
                />

                {/* Fuentes Activas */}
                <StatCard
                    title="Fuentes Activas"
                    value={`${stats?.active_sources || 0}/${stats?.total_sources || 0}`}
                    icon={Wifi}
                    color="purple"
                    loading={isLoading}
                />

                {/* Eventos Raw */}
                <StatCard
                    title="Eventos Raw Capturados"
                    value={stats?.total_raw_events || 0}
                    icon={Database}
                    color="blue"
                    loading={isLoading}
                />
            </div>

            {/* Estado del Sistema */}
            <div className="card">
                <h3 className="text-lg font-semibold text-white mb-4">Estado del Sistema</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Distribución por Estado */}
                    <div>
                        <h4 className="text-sm font-medium text-gray-400 mb-3">Distribución por Estado</h4>
                        <div className="space-y-3">
                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm text-gray-300">Confirmados</span>
                                    <span className="text-sm font-semibold text-green-400">{confirmados}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-green-500 h-2 rounded-full transition-all duration-500"
                                        style={{ width: `${totalEvents > 0 ? (confirmados / totalEvents) * 100 : 0}%` }}
                                        role="progressbar"
                                        aria-valuenow={confirmados}
                                        aria-valuemin={0}
                                        aria-valuemax={totalEvents}
                                        aria-label={`Eventos confirmados: ${confirmados} de ${totalEvents}`}
                                    />
                                </div>
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm text-gray-300">En Verificación</span>
                                    <span className="text-sm font-semibold text-yellow-400">{enVerificacion}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-yellow-500 h-2 rounded-full transition-all duration-500"
                                        style={{ width: `${totalEvents > 0 ? (enVerificacion / totalEvents) * 100 : 0}%` }}
                                        role="progressbar"
                                        aria-valuenow={enVerificacion}
                                        aria-valuemin={0}
                                        aria-valuemax={totalEvents}
                                        aria-label={`Eventos en verificación: ${enVerificacion} de ${totalEvents}`}
                                    />
                                </div>
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm text-gray-300">No Verificados</span>
                                    <span className="text-sm font-semibold text-red-400">{noVerificados}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-red-500 h-2 rounded-full transition-all duration-500"
                                        style={{ width: `${totalEvents > 0 ? (noVerificados / totalEvents) * 100 : 0}%` }}
                                        role="progressbar"
                                        aria-valuenow={noVerificados}
                                        aria-valuemin={0}
                                        aria-valuemax={totalEvents}
                                        aria-label={`Eventos no verificados: ${noVerificados} de ${totalEvents}`}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Información del Sistema */}
                    <div>
                        <h4 className="text-sm font-medium text-gray-400 mb-3">Información del Sistema</h4>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between py-2 border-b border-midnight-border">
                                <span className="text-sm text-gray-300">Último Scraping</span>
                                <span className="text-sm font-medium text-white">
                                    {stats?.last_scraping
                                        ? new Date(stats.last_scraping).toLocaleString('es-ES', {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                            day: '2-digit',
                                            month: 'short'
                                        })
                                        : 'N/A'}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-midnight-border">
                                <span className="text-sm text-gray-300">Tasa de Confirmación</span>
                                <span className="text-sm font-semibold text-green-400">
                                    {confirmedPercentage}%
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2">
                                <span className="text-sm text-gray-300">Estado del Sistema</span>
                                <span className="inline-flex items-center gap-2 px-2 py-1 rounded-full bg-green-500/20 text-green-400 border border-green-500/30 text-xs">
                                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                                    Operativo
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
