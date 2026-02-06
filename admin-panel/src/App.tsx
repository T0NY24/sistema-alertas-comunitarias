import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { Dashboard } from './components/dashboard/Dashboard';
import { EventsTable } from './components/events/EventsTable';
import { SimulationModule } from './components/simulation/SimulationModule';
import { ServicesPanel } from './components/services/ServicesPanel';
import { useCreateEvent } from './api/endpoints';
import { LayoutDashboard, Table2, Zap, Server } from 'lucide-react';
import './index.css';

// Crear QueryClient para React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

type View = 'dashboard' | 'events' | 'simulation' | 'services';

// Componente interno que usa los hooks de React Query
function AppContent() {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const createEventMutation = useCreateEvent();

  const handleSimulationSubmit = (eventData: any) => {
    createEventMutation.mutate(eventData, {
      onSuccess: () => {
        alert('✅ Evento creado exitosamente!');
        setCurrentView('events'); // Cambiar a vista de eventos para ver el nuevo evento
      },
      onError: (error: any) => {
        alert(`❌ Error al crear evento: ${error.message}`);
      }
    });
  };

  return (
    <div className="min-h-screen bg-midnight-bg">
      {/* Header */}
      <header className="bg-midnight-card border-b border-midnight-border sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                SACV Command Center
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                Sistema de Alertas Comunitarias Verificadas
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 text-green-400 border border-green-500/30 text-sm">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                Sistema Activo
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="mt-4 flex gap-2" role="navigation" aria-label="Navegación principal">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${currentView === 'dashboard'
                ? 'bg-midnight-accent text-white'
                : 'text-gray-400 hover:text-white hover:bg-midnight-bg'
                }`}
              aria-current={currentView === 'dashboard' ? 'page' : undefined}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView('events')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${currentView === 'events'
                ? 'bg-midnight-accent text-white'
                : 'text-gray-400 hover:text-white hover:bg-midnight-bg'
                }`}
              aria-current={currentView === 'events' ? 'page' : undefined}
            >
              <Table2 className="w-4 h-4" />
              Eventos
            </button>
            <button
              onClick={() => setCurrentView('simulation')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${currentView === 'simulation'
                ? 'bg-midnight-accent text-white'
                : 'text-gray-400 hover:text-white hover:bg-midnight-bg'
                }`}
              aria-current={currentView === 'simulation' ? 'page' : undefined}
            >
              <Zap className="w-4 h-4" />
              Simulación
            </button>
            <button
              onClick={() => setCurrentView('services')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${currentView === 'services'
                ? 'bg-midnight-accent text-white'
                : 'text-gray-400 hover:text-white hover:bg-midnight-bg'
                }`}
              aria-current={currentView === 'services' ? 'page' : undefined}
            >
              <Server className="w-4 h-4" />
              Servicios
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'events' && <EventsTable />}
        {currentView === 'simulation' && (
          <SimulationModule
            onSubmit={handleSimulationSubmit}
            isLoading={createEventMutation.isPending}
          />
        )}
        {currentView === 'services' && <ServicesPanel />}
      </main>

      {/* Footer */}
      <footer className="bg-midnight-card border-t border-midnight-border mt-12">
        <div className="container mx-auto px-4 py-4">
          <p className="text-center text-sm text-gray-400">
            SACV v1.0 - Command Center Dashboard
          </p>
        </div>
      </footer>
    </div>
  );
}

// App wrapper con QueryClientProvider
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
