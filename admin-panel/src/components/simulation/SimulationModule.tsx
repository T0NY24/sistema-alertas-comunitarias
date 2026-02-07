import React, { useState, useMemo } from 'react';
import { AlertCircle, CloudRain, Zap, Activity, Globe } from 'lucide-react';
import { useProvinces } from '../../api/endpoints';

interface PanicButtonProps {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    type: string;
    severity: 'Alta' | 'Media' | 'Baja';
    color: string;
    onClick: (type: string, severity: string) => void;
}

const PanicButton: React.FC<PanicButtonProps> = ({ icon: Icon, label, type, severity, color, onClick }) => {
    return (
        <button
            onClick={() => onClick(type, severity)}
            className={`flex flex-col items-center justify-center p-6 rounded-lg border-2 transition-all hover:scale-105 ${color}`}
        >
            <Icon className="w-12 h-12 mb-2" />
            <span className="font-semibold text-sm">{label}</span>
            <span className="text-xs mt-1 opacity-75">Severidad: {severity}</span>
        </button>
    );
};

interface SimulationFormProps {
    onSubmit: (event: any) => void;
    onMassSimulation?: (events: any[]) => Promise<void>;
    isLoading: boolean;
}

export const SimulationModule: React.FC<SimulationFormProps> = ({ onSubmit, onMassSimulation, isLoading }) => {
    const { data: provinces = [] } = useProvinces();
    const [isMassSimulating, setIsMassSimulating] = useState(false);

    const [formData, setFormData] = useState({
        type: 'sismo',
        severity: 'Media',
        zone: '',
        province_id: provinces[0]?.province_id || null,
        title: '',
        description: '',
        evidence_url: ''
    });

    // Mapeo de provincias comunes (hardcode por ahora)
    const provinceNameToId: Record<string, number> = useMemo(() => {
        const mapping: Record<string, number> = {};
        provinces.forEach((p: any) => {
            mapping[p.name.toUpperCase()] = p.province_id;
        });
        return mapping;
    }, [provinces]);

    const handleQuickEvent = (type: string, severity: string) => {
        const quickEvents = {
            sismo: {
                title: `Sismo detectado - Magnitud ${severity === 'Alta' ? '6.5' : severity === 'Media' ? '5.0' : '3.5'}`,
                description: `Evento sísmico registrado por sensores automáticos. Profundidad estimada: ${severity === 'Alta' ? '10km' : '25km'}`,
                zone: 'Pichincha',
                evidence_url: 'https://earthquake.usgs.gov/earthquakes/eventpage/test'
            },
            lluvia: {
                title: `Alerta de lluvia ${severity.toLowerCase()}`,
                description: `Precipitaciones intensas registradas. Acumulado: ${severity === 'Alta' ? '50mm/h' : severity === 'Media' ? '25mm/h' : '10mm/h'}`,
                zone: 'Guayas',
                evidence_url: 'https://openweathermap.org/city/test'
            },
            corte: {
                title: `Corte de energía - Nivel ${severity}`,
                description: `Interrupción del servicio eléctrico reportada. Afectación estimada: ${severity === 'Alta' ? '> 10,000 usuarios' : severity === 'Media' ? '1,000-10,000 usuarios' : '< 1,000 usuarios'}`,
                zone: 'Azuay',
                evidence_url: 'https://www.cnel.gob.ec/cortes-programados'
            }
        };

        const eventData = {
            type,
            severity,
            ...(quickEvents[type as keyof typeof quickEvents] || quickEvents.sismo),
            province_id: provinceNameToId[quickEvents[type as keyof typeof quickEvents]?.zone?.toUpperCase() || 'PICHINCHA'] || null,
            source_id: null, // Manual event
            status: 'CONFIRMADO',
            score: 100
        };

        onSubmit(eventData);
    };

    const handleManualSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({
            ...formData,
            source_id: null,
            status: 'CONFIRMADO' // Cambiar a CONFIRMADO por defecto para que envíe notificaciones
        });
    };

    const handleMassSimulation = async () => {
        if (!onMassSimulation || isMassSimulating) return;

        setIsMassSimulating(true);

        try {
            // Tipos de eventos para variar
            const eventTypes = [
                { type: 'sismo', severity: 'Alta', icon: '🌋' },
                { type: 'lluvia', severity: 'Media', icon: '🌧️' },
                { type: 'corte', severity: 'Baja', icon: '⚡' }
            ];

            // Crear un evento para cada provincia
            const events = provinces.map((province: any, index: number) => {
                const eventType = eventTypes[index % eventTypes.length];

                return {
                    type: eventType.type,
                    severity: eventType.severity,
                    zone: province.name,
                    province_id: province.province_id,
                    title: `${eventType.icon} ${eventType.type.toUpperCase()} en ${province.name}`,
                    description: `Evento de prueba masiva generado automáticamente para ${province.name}. Severidad: ${eventType.severity}`,
                    evidence_url: 'https://ejemplo.com/prueba-masiva',
                    status: 'CONFIRMADO', // Importante: CONFIRMADO para enviar notificaciones
                    source_id: null,
                    score: 100
                };
            });

            await onMassSimulation(events);
        } finally {
            setIsMassSimulating(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <AlertCircle className="w-6 h-6 text-red-400" />
                    Simulador de Eventos
                </h2>
                <p className="text-sm text-gray-400 mt-1">
                    Crear eventos de prueba para testing del sistema de alertas
                </p>
            </div>

            {/* Panic Buttons */}
            <div className="card">
                <h3 className="text-lg font-semibold text-white mb-4">Botones de Pánico (Quick Events)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <PanicButton
                        icon={Activity}
                        label="Sismo Alto"
                        type="sismo"
                        severity="Alta"
                        color="border-red-500 text-red-400 hover:bg-red-500/10"
                        onClick={handleQuickEvent}
                    />
                    <PanicButton
                        icon={Activity}
                        label="Sismo Medio"
                        type="sismo"
                        severity="Media"
                        color="border-yellow-500 text-yellow-400 hover:bg-yellow-500/10"
                        onClick={handleQuickEvent}
                    />
                    <PanicButton
                        icon={CloudRain}
                        label="Lluvia Intensa"
                        type="lluvia"
                        severity="Alta"
                        color="border-blue-500 text-blue-400 hover:bg-blue-500/10"
                        onClick={handleQuickEvent}
                    />
                    <PanicButton
                        icon={CloudRain}
                        label="Lluvia Moderada"
                        type="lluvia"
                        severity="Media"
                        color="border-blue-400 text-blue-300 hover:bg-blue-400/10"
                        onClick={handleQuickEvent}
                    />
                    <PanicButton
                        icon={Zap}
                        label="Corte Masivo"
                        type="corte"
                        severity="Alta"
                        color="border-orange-500 text-orange-400 hover:bg-orange-500/10"
                        onClick={handleQuickEvent}
                    />
                    <PanicButton
                        icon={Zap}
                        label="Corte Localizado"
                        type="corte"
                        severity="Baja"
                        color="border-orange-300 text-orange-300 hover:bg-orange-300/10"
                        onClick={handleQuickEvent}
                    />
                </div>
            </div>

            {/* Mass Simulation - 24 Provinces */}
            {onMassSimulation && (
                <div className="card bg-gradient-to-r from-purple-900/20 to-blue-900/20 border-purple-500/30">
                    <div className="flex items-start gap-4">
                        <Globe className="w-12 h-12 text-purple-400 flex-shrink-0" />
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-white mb-2">
                                🇪🇨 Simulación Masiva Nacional
                            </h3>
                            <p className="text-sm text-gray-300 mb-4">
                                Crea eventos de prueba para <strong>las 24 provincias de Ecuador</strong> con un solo clic.
                                Cada provincia recibirá un evento diferente (SISMO, LLUVIA, CORTE) marcado como CONFIRMADO.
                            </p>
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={handleMassSimulation}
                                    disabled={isMassSimulating || provinces.length === 0}
                                    className="btn-primary bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 flex items-center gap-2"
                                >
                                    {isMassSimulating ? (
                                        <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                            Enviando a {provinces.length} provincias...
                                        </>
                                    ) : (
                                        <>
                                            <Globe className="w-4 h-4" />
                                            Simular en 24 Provincias
                                        </>
                                    )}
                                </button>
                                {provinces.length > 0 && (
                                    <span className="text-xs text-gray-400">
                                        📊 {provinces.length} provincias detectadas
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Manual Event Form */}
            <div className="card">
                <h3 className="text-lg font-semibold text-white mb-4">Crear Evento Personalizado</h3>
                <form onSubmit={handleManualSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Type */}
                        <div>
                            <label htmlFor="event-type" className="block text-sm font-medium text-gray-300 mb-2">
                                Tipo de Evento
                            </label>
                            <select
                                id="event-type"
                                className="input-field"
                                value={formData.type}
                                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                aria-label="Seleccionar tipo de evento"
                            >
                                <option value="sismo">Sismo</option>
                                <option value="lluvia">Lluvia</option>
                                <option value="corte">Corte de Energía</option>
                            </select>
                        </div>

                        {/* Severity */}
                        <div>
                            <label htmlFor="event-severity" className="block text-sm font-medium text-gray-300 mb-2">
                                Severidad
                            </label>
                            <select
                                id="event-severity"
                                className="input-field"
                                value={formData.severity}
                                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                                aria-label="Seleccionar severidad del evento"
                            >
                                <option value="Alta">Alta</option>
                                <option value="Media">Media</option>
                                <option value="Baja">Baja</option>
                            </select>
                        </div>
                    </div>

                    {/* Province */}
                    <div>
                        <label htmlFor="event-province" className="block text-sm font-medium text-gray-300 mb-2">
                            Provincia *
                        </label>
                        <select
                            id="event-province"
                            className="input-field"
                            value={formData.province_id || ''}
                            onChange={(e) => setFormData({ ...formData, province_id: e.target.value ? parseInt(e.target.value) : null, zone: provinces.find((p: any) => p.province_id === parseInt(e.target.value))?.name || '' })}
                            required
                            aria-label="Seleccionar provincia"
                        >
                            <option value="">Seleccionar provincia...</option>
                            {provinces.map((province: any) => (
                                <option key={province.province_id} value={province.province_id}>
                                    {province.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Title */}
                    <div>
                        <label htmlFor="event-title" className="block text-sm font-medium text-gray-300 mb-2">
                            Título *
                        </label>
                        <input
                            id="event-title"
                            type="text"
                            className="input-field"
                            placeholder="Ej: Sismo de magnitud 5.5 en Quito"
                            value={formData.title}
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            required
                            aria-label="Ingresar título del evento"
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label htmlFor="event-description" className="block text-sm font-medium text-gray-300 mb-2">
                            Descripción
                        </label>
                        <textarea
                            id="event-description"
                            className="input-field"
                            rows={3}
                            placeholder="Descripción detallada del evento..."
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            aria-label="Ingresar descripción del evento"
                        />
                    </div>

                    {/* Evidence URL */}
                    <div>
                        <label htmlFor="event-evidence" className="block text-sm font-medium text-gray-300 mb-2">
                            URL de Evidencia
                        </label>
                        <input
                            id="event-evidence"
                            type="url"
                            className="input-field"
                            placeholder="https://..."
                            value={formData.evidence_url}
                            onChange={(e) => setFormData({ ...formData, evidence_url: e.target.value })}
                            aria-label="Ingresar URL de evidencia"
                        />
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={isLoading || !formData.title}
                        className="btn-primary w-full flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                Creando evento...
                            </>
                        ) : (
                            <>
                                <AlertCircle className="w-4 h-4" />
                                Crear Evento de Prueba
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};
