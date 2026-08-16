import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import type { NavTab } from './components/layout/Sidebar';
import { LoginView } from './components/views/LoginView';
import { DashboardView } from './components/views/DashboardView';
import { PersonasAccesosView } from './components/views/PersonasAccesosView';
import { DiagnosticosView } from './components/views/DiagnosticosView';
import { useMecanicos } from './hooks/useMecanicos';
import { useDiagnosticos } from './hooks/useDiagnosticos';
import { useMetricas } from './hooks/useMetricas';
import type { UsuarioSesion, Diagnostico } from './types';
import { apiService, SESSION_EXPIRED_EVENT, SESSION_UPDATED_EVENT } from './services/api';
import { getValidRoute } from './utils/routing';
import type { AppRoute } from './utils/routing';

export type { AppRoute };

const LAST_ROUTE_KEY = 'carbot_last_route';

const readLastRoute = (): AppRoute => {
  const saved = localStorage.getItem(LAST_ROUTE_KEY);
  return ['/inicio', '/personas', '/diagnosticos'].includes(saved || '')
    ? saved as AppRoute
    : '/inicio';
};

const isAdminSession = (user: UsuarioSesion | null): user is UsuarioSesion =>
  Boolean(user && ['administrador', 'admin'].includes(user.rol));

const readAdminSession = (): UsuarioSesion | null => {
  try {
    const saved = localStorage.getItem('carbot_session');
    if (!saved) return null;
    const parsed = JSON.parse(saved) as UsuarioSesion;
    if (isAdminSession(parsed)) return parsed;
  } catch {
    // Una sesión dañada o antigua se elimina abajo.
  }
  localStorage.removeItem('carbot_session');
  return null;
};

export const App: React.FC = () => {
  // Session state
  const [user, setUser] = useState<UsuarioSesion | null>(() => {
    return readAdminSession();
  });

  // App route state (HTML5 History API)
  const [currentRoute, setCurrentRoute] = useState<AppRoute>(() => {
    const parsedUser = readAdminSession();
    const requestedPath = window.location.pathname;
    if (!parsedUser && ['/inicio', '/personas', '/diagnosticos'].includes(requestedPath)) {
      localStorage.setItem(LAST_ROUTE_KEY, requestedPath);
    }
    const pathToRestore = parsedUser && requestedPath === '/login' ? readLastRoute() : requestedPath;
    const initialRoute = getValidRoute(pathToRestore, parsedUser);
    if (window.location.pathname !== initialRoute) {
      window.history.replaceState({}, '', initialRoute);
    }
    return initialRoute;
  });

  const [solicitudesPendientesCount, setSolicitudesPendientesCount] = useState<number>(0);
  const [isDesktopCollapsed, setIsDesktopCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const navigate = useCallback((path: AppRoute) => {
    if (path !== '/login') localStorage.setItem(LAST_ROUTE_KEY, path);
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path);
    }
    setCurrentRoute(path);
  }, []);

  // Mantiene React sincronizado cuando api.ts renueva o agota la sesión.
  useEffect(() => {
    const handleSessionUpdated = (event: Event) => {
      const session = (event as CustomEvent<UsuarioSesion>).detail;
      if (isAdminSession(session)) setUser(session);
    };
    const handleSessionExpired = () => {
      if (currentRoute !== '/login') localStorage.setItem(LAST_ROUTE_KEY, currentRoute);
      setUser(null);
      if (window.location.pathname !== '/login') {
        window.history.replaceState({}, '', '/login');
      }
      setCurrentRoute('/login');
    };

    window.addEventListener(SESSION_UPDATED_EVENT, handleSessionUpdated);
    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () => {
      window.removeEventListener(SESSION_UPDATED_EVENT, handleSessionUpdated);
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    };
  }, [currentRoute]);

  const handleToggleSidebar = () => {
    if (window.innerWidth <= 768) {
      setIsMobileSidebarOpen((prev) => !prev);
    } else {
      setIsDesktopCollapsed((prev) => !prev);
    }
  };

  // Custom Hooks for Modular Architecture
  const { metricas, cargando: cargandoMetricas, cargarMetricas } = useMetricas();
  const {
    mecanicos,
    cargarMecanicos,
  } = useMecanicos();
  const {
    diagnosticos,
    cargando: cargandoDiagnosticos,
    cargarDiagnosticos,
    actualizarEstado,
  } = useDiagnosticos();

  // Selected diagnostic modal state
  const [diagnosticoSeleccionado, setDiagnosticoSeleccionado] = useState<Diagnostico | null>(null);

  // Fetch pending requests count (only for administrative roles)
  const cargarSolicitudesPendientesCount = useCallback(async () => {
    if (!isAdminSession(user)) {
      setSolicitudesPendientesCount(0);
      return;
    }
    try {
      const lista = await apiService.getSolicitudesAcceso('pendiente');
      setSolicitudesPendientesCount(Array.isArray(lista) ? lista.length : 0);
    } catch (err) {
      console.error('Error al cargar solicitudes pendientes:', err);
    }
  }, [user]);

  const handleRecargarPersonas = useCallback(() => {
    cargarSolicitudesPendientesCount();
  }, [cargarSolicitudesPendientesCount]);

  const activeTab: NavTab = currentRoute === '/personas' ? 'personas' : currentRoute === '/diagnosticos' ? 'diagnosticos' : 'inicio';

  // Load module data on demand when tab changes
  useEffect(() => {
    if (!user) return;
    if (activeTab === 'inicio') {
      cargarMetricas();
    } else if (activeTab === 'diagnosticos') {
      cargarDiagnosticos();
      cargarMecanicos();
    } else if (activeTab === 'personas') {
      cargarSolicitudesPendientesCount();
    }
  }, [user, activeTab, cargarMetricas, cargarDiagnosticos, cargarMecanicos, cargarSolicitudesPendientesCount]);

  // Initial badge count load for non-mechanic users
  useEffect(() => {
    if (isAdminSession(user)) {
      cargarSolicitudesPendientesCount();
    }
  }, [user, cargarSolicitudesPendientesCount]);

  // Sync route on popstate (browser back/forward buttons)
  useEffect(() => {
    const handlePopState = () => {
      const targetRoute = getValidRoute(window.location.pathname, user);
      if (window.location.pathname !== targetRoute) {
        window.history.replaceState({}, '', targetRoute);
      }
      setCurrentRoute(targetRoute);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [user]);

  // Sync route state if user state changes
  useEffect(() => {
    const valid = getValidRoute(window.location.pathname, user);
    if (window.location.pathname !== valid) {
      window.history.replaceState({}, '', valid);
    }
    setCurrentRoute(valid);
  }, [user]);

  const handleLoginSuccess = (usuarioSesion: UsuarioSesion) => {
    if (!isAdminSession(usuarioSesion)) {
      localStorage.removeItem('carbot_session');
      setUser(null);
      setCurrentRoute('/login');
      return;
    }
    setUser(usuarioSesion);
    localStorage.setItem('carbot_session', JSON.stringify(usuarioSesion));
    const restoredRoute = getValidRoute(readLastRoute(), usuarioSesion);
    if (window.location.pathname !== restoredRoute) {
      window.history.pushState({}, '', restoredRoute);
    }
    setCurrentRoute(restoredRoute);
  };

  const handleLogout = () => {
    if (currentRoute !== '/login') localStorage.setItem(LAST_ROUTE_KEY, currentRoute);
    setUser(null);
    localStorage.removeItem('carbot_session');
    if (window.location.pathname !== '/login') {
      window.history.pushState({}, '', '/login');
    }
    setCurrentRoute('/login');
  };

  if (!isAdminSession(user) || currentRoute === '/login') {
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
          user={user}
          activeTab={activeTab}
          onSelectTab={(tab: NavTab) => navigate(`/${tab}` as AppRoute)}
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
          isDesktopCollapsed={isDesktopCollapsed}
          solicitudesPendientesCount={solicitudesPendientesCount}
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
          {activeTab === 'inicio' && (
            <DashboardView
              metricas={metricas}
              cargando={cargandoMetricas}
              onFiltrarMetricas={cargarMetricas}
              onIrAMecanicos={() => navigate('/personas')}
            />
          )}

          {activeTab === 'personas' && (
            <PersonasAccesosView
              user={user}
              onRecargarMecanicos={handleRecargarPersonas}
            />
          )}

          {activeTab === 'diagnosticos' && (
            <DiagnosticosView
              diagnosticos={diagnosticos}
              cargando={cargandoDiagnosticos}
              mecanicos={mecanicos}
              currentUser={user}
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
