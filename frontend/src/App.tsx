import React, { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import type { NavTab } from './components/layout/Sidebar';
import { LoginView } from './components/views/LoginView';
import { DashboardView } from './components/views/DashboardView';
import { MecanicosView } from './components/views/MecanicosView';
import { ClientesSolicitudesView } from './components/views/ClientesSolicitudesView';
import { DiagnosticosView } from './components/views/DiagnosticosView';
import { useMecanicos } from './hooks/useMecanicos';
import { useDiagnosticos } from './hooks/useDiagnosticos';
import { useMetricas } from './hooks/useMetricas';
import type { UsuarioSesion, Diagnostico } from './types';

export const App: React.FC = () => {
  // Session state
  const [user, setUser] = useState<UsuarioSesion | null>(() => {
    const saved = localStorage.getItem('carbot_session');
    return saved ? JSON.parse(saved) : null;
  });

  // App navigation & drawer state
  const [activeTab, setActiveTab] = useState<NavTab>('resumen');
  const [isDesktopCollapsed, setIsDesktopCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const handleToggleSidebar = () => {
    if (window.innerWidth <= 768) {
      setIsMobileSidebarOpen((prev) => !prev);
    } else {
      setIsDesktopCollapsed((prev) => !prev);
    }
  };

  // Custom Hooks for Modular Architecture
  const { metricas, cargarMetricas } = useMetricas();
  const {
    mecanicos,
    cargarMecanicos,
    registrarMecanico,
    toggleActivar,
    toggleBloquear,
    eliminarMecanico,
    cambiarRol,
  } = useMecanicos();
  const {
    diagnosticos,
    cargarDiagnosticos,
    actualizarEstado,
  } = useDiagnosticos();

  // Selected diagnostic modal state
  const [diagnosticoSeleccionado, setDiagnosticoSeleccionado] = useState<Diagnostico | null>(null);

  // Load data on start / user session change
  useEffect(() => {
    if (user) {
      cargarMetricas();
      cargarMecanicos();
      cargarDiagnosticos();
    }
  }, [user, cargarMetricas, cargarMecanicos, cargarDiagnosticos]);

  const handleLoginSuccess = (usuarioSesion: UsuarioSesion) => {
    setUser(usuarioSesion);
    localStorage.setItem('carbot_session', JSON.stringify(usuarioSesion));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('carbot_session');
  };

  if (!user) {
    return <LoginView onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-main)' }}>
      {/* Top Header */}
      <Header
        user={user}
        onLogout={handleLogout}
        onToggleMobileSidebar={handleToggleSidebar}
      />

      {/* Main Workspace Layout */}
      <div style={{ display: 'flex', flex: 1 }}>
        {/* Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
          isDesktopCollapsed={isDesktopCollapsed}
        />

        {/* Dynamic Content Body */}
        <main
          style={{
            flex: 1,
            padding: '24px 32px',
            width: '100%',
            maxWidth: '100%',
          }}
          className="app-main-content"
        >
          {activeTab === 'resumen' && metricas && (
            <DashboardView
              metricas={metricas}
              onFiltrarMetricas={cargarMetricas}
              onIrAMecanicos={() => setActiveTab('mecanicos')}
            />
          )}

          {activeTab === 'clientes' && (
            <ClientesSolicitudesView onRecargarMecanicos={cargarMecanicos} />
          )}

          {activeTab === 'mecanicos' && (
            <MecanicosView
              mecanicos={mecanicos}
              onRegistrarMecanico={registrarMecanico}
              onToggleActivar={toggleActivar}
              onToggleBloquear={toggleBloquear}
              onEliminarMecanico={eliminarMecanico}
              onCambiarRol={cambiarRol}
            />
          )}

          {activeTab === 'diagnosticos' && (
            <DiagnosticosView
              diagnosticos={diagnosticos}
              mecanicos={mecanicos}
              onActualizarEstado={actualizarEstado}
              onFiltrar={cargarDiagnosticos}
              diagnosticoSeleccionadoModal={diagnosticoSeleccionado}
              onCerrarModalDetalle={() => setDiagnosticoSeleccionado(null)}
              onAbrirModalDetalle={(diag) => setDiagnosticoSeleccionado(diag)}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
