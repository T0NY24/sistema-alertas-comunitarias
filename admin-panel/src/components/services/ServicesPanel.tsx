import React, { useState } from 'react';
import { Server, RefreshCw, CheckCircle, XCircle, Activity } from 'lucide-react';

interface Container {
    name: string;
    status: string;
    state: string;
    image: string;
    created: string;
}

export const ServicesPanel: React.FC = () => {
    const [containers, setContainers] = useState<Container[]>([]);
    const [loading, setLoading] = useState(true);
    const [restarting, setRestarting] = useState<string | null>(null);

    React.useEffect(() => {
        fetchContainers();
        // Refrescar cada 10 segundos
        const interval = setInterval(fetchContainers, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchContainers = async () => {
        try {
            const response = await fetch('http://217.216.67.99:8001/api/containers');
            if (response.ok) {
                const data = await response.json();
                setContainers(data);
            }
        } catch (error) {
            console.error('Error fetching containers:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRestart = async (containerName: string) => {
        if (!confirm(`¿Reiniciar ${containerName}?`)) return;

        setRestarting(containerName);
        try {
            const response = await fetch(`http://217.216.67.99:8001/api/containers/${containerName}/restart`, {
                method: 'POST',
            });

            if (response.ok) {
                alert(`✅ ${containerName} reiniciado correctamente`);
                // Esperar 2 segundos y refrescar la lista
                setTimeout(fetchContainers, 2000);
            } else {
                const error = await response.json();
                alert(`❌ Error: ${error.detail}`);
            }
        } catch (error: any) {
            alert(`❌ Error: ${error.message}`);
        } finally {
            setRestarting(null);
        }
    };

    const getStatusColor = (status: string) => {
        if (status === 'running') return 'text-green-400';
        if (status === 'exited') return 'text-red-400';
        return 'text-yellow-400';
    };

    const getStatusIcon = (status: string) => {
        if (status === 'running') return <CheckCircle className="w-5 h-5 text-green-400" />;
        if (status === 'exited') return <XCircle className="w-5 h-5 text-red-400" />;
        return <Activity className="w-5 h-5 text-yellow-400" />;
    };

    if (loading) {
        return (
            <div className="card">
                <div className="flex items-center justify-center py-12">
                    <div className="flex items-center gap-3">
                        <div className="spinner"></div>
                        <span className="text-gray-400">Cargando contenedores...</span>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="card">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Server className="w-6 h-6 text-midnight-accent" />
                        Microservicios Docker
                    </h2>
                    <button
                        onClick={fetchContainers}
                        className="btn btn-secondary flex items-center gap-2"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refrescar
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {containers.map((container) => (
                        <div
                            key={container.name}
                            className="card bg-midnight-card border border-midnight-border p-4"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    {getStatusIcon(container.status)}
                                    <div>
                                        <h3 className="text-sm font-semibold text-white">
                                            {container.name.replace('sacv_', '')}
                                        </h3>
                                        <p className="text-xs text-gray-500">{container.name}</p>
                                    </div>
                                </div>
                                <span
                                    className={`text-xs font-semibold uppercase ${getStatusColor(container.status)}`}
                                >
                                    {container.status}
                                </span>
                            </div>

                            <div className="space-y-2 mb-4">
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-gray-400">Estado:</span>
                                    <span className="text-gray-300">{container.state}</span>
                                </div>
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-gray-400">Imagen:</span>
                                    <span className="text-gray-300 truncate max-w-[150px]" title={container.image}>
                                        {container.image}
                                    </span>
                                </div>
                            </div>

                            <button
                                onClick={() => handleRestart(container.name)}
                                disabled={restarting === container.name || container.status !== 'running'}
                                className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded bg-midnight-accent/20 text-midnight-accent border border-midnight-accent/30 text-sm font-semibold hover:bg-midnight-accent/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {restarting === container.name ? (
                                    <>
                                        <div className="spinner-sm"></div>
                                        Reiniciando...
                                    </>
                                ) : (
                                    <>
                                        <RefreshCw className="w-4 h-4" />
                                        Reiniciar
                                    </>
                                )}
                            </button>
                        </div>
                    ))}
                </div>

                {containers.length === 0 && (
                    <div className="text-center py-12">
                        <Server className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                        <p className="text-gray-400">No se encontraron contenedores</p>
                    </div>
                )}
            </div>
        </div>
    );
};
