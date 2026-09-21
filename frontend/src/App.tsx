import React, { useState, useEffect, useCallback } from 'react';
import { LoginView } from './features/auth';
import { DashboardView } from './features/dashboard';
import {

  GestionChatbotView,
  type GestionSubTab,
  useDiagnosticos,
  useMecanicos,
} from './features/management';
import { ProyectoCarbotView } from './features/project';
import {
  apiService,
  SESSION_EXPIRED_EVENT,
  SESSION_UPDATED_EVENT,
} from './shared/api';
import { Header, Sidebar, type NavTab } from './shared/layout';
import { getValidRoute, type AppRoute } from './shared/routing';
import type {
  Diagnostico,
  SolicitudAcceso,
  UsuarioSesion,
} from './shared/types';

export type { AppRoute };

const LAST_ROUTE_KEY = 'carbot_last_route';

const readLastRoute = (): AppRoute => {
  const saved = localStorage.getItem(LAST_ROUTE_KEY);
  return ['/inicio', '/gestion', '/proyecto', '/personas', '/diagnosticos', '/validacion', '/fichas'].includes(saved || '')
    ? (saved === '/personas' || saved === '/diagnosticos' ? '/gestion' : saved) as AppRoute
    : '/inicio';
};

const isAdminSession = (user: UsuarioSesion | null): user is UsuarioSesion =>
  Boolean(user && ['administrador', 'admin'].includes(user.rol));

const readAdminSession = (): UsuarioSesion | null => {
  try {
    const saved = localStorage.getItem('carbot_session');
    if (!saved) return null;
    const parsed = JSON.parse(saved) as UsuarioSesion;
    if (isAdminSession(parsed)) {
      const safeSession: UsuarioSesion = {
        id: parsed.id,
        username: parsed.username,
        nombre: parsed.nombre,
        rol: parsed.rol,
        taller: parsed.taller,
      };
      localStorage.setItem('carbot_session', JSON.stringify(safeSession));
      return safeSession;
    }
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

  const [solicitudes, setSolicitudes] = useState<SolicitudAcceso[]>([]);
  const [cargandoSolicitudes, setCargandoSolicitudes] = useState(false);
  const [errorSolicitudes, setErrorSolicitudes] = useState<string | null>(null);
  const [gestionSubTab, setGestionSubTab] = useState<GestionSubTab>('solicitudes');
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
  const {
    mecanicos,

    cargando: cargandoMecanicos,
    error: errorMecanicos,
    cargarMecanicos,
  } = useMecanicos();
  const {
    diagnosticos,
    total: totalDiagnosticos,
    cargando: cargandoDiagnosticos,
    error: errorDiagnosticos,
    cargarDiagnosticos,
  } = useDiagnosticos();

  // Selected diagnostic modal state
  const [diagnosticoSeleccionado, setDiagnosticoSeleccionado] = useState<Diagnostico | null>(null);

  // Fetch all access requests
  const cargarSolicitudes = useCallback(async () => {
    if (!isAdminSession(user)) {
      setSolicitudes([]);
      return;
    }
    try {
      setCargandoSolicitudes(true);
      setErrorSolicitudes(null);
      const lista = await apiService.getSolicitudesAcceso();
      setSolicitudes(Array.isArray(lista) ? lista : []);
    } catch (err) {
      console.error('Error al cargar solicitudes:', err);
      setErrorSolicitudes(err instanceof Error ? err.message : 'Error al cargar las solicitudes');
    } finally {
      setCargandoSolicitudes(false);
    }
  }, [user]);

  const solicitudesPendientesCount = solicitudes.filter((s) => s.estado === 'pendiente').length;

  const handleRecargarGestion = useCallback(async () => {
    await Promise.all([cargarSolicitudes(), cargarMecanicos(), cargarDiagnosticos()]);
  }, [cargarSolicitudes, cargarMecanicos, cargarDiagnosticos]);

  const activeTab: NavTab =
    currentRoute === '/gestion' || currentRoute === '/personas' || currentRoute === '/diagnosticos'
      ? 'gestion'
      : currentRoute === '/proyecto'
      ? 'proyecto'
      : 'inicio';

  // Load module data on demand when tab changes
  useEffect(() => {
    if (!user) return;
    if (activeTab === 'inicio') {
      cargarSolicitudes();
    } else if (activeTab === 'gestion') {
      handleRecargarGestion();
    }
  }, [user, activeTab, cargarSolicitudes, handleRecargarGestion]);


  // Initial badge count load for non-mechanic users
  useEffect(() => {
    if (isAdminSession(user)) {
      cargarSolicitudes();
    }
  }, [user, cargarSolicitudes]);

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
      localStorage.removeItem(LAST_ROUTE_KEY);
      setUser(null);
      setCurrentRoute('/login');
      return;
    }
    setUser(usuarioSesion);
    apiService.setAccessToken(usuarioSesion.token || null);
    const safeSession: UsuarioSesion = {
      id: usuarioSesion.id,
      username: usuarioSesion.username,
      nombre: usuarioSesion.nombre,
      rol: usuarioSesion.rol,
      taller: usuarioSesion.taller,
    };
    localStorage.setItem('carbot_session', JSON.stringify(safeSession));
    localStorage.setItem(LAST_ROUTE_KEY, '/inicio');
    if (window.location.pathname !== '/inicio') {
      window.history.pushState({}, '', '/inicio');
    }
    setCurrentRoute('/inicio');
  };

  const handleLogout = () => {
    void apiService.logout();
    localStorage.removeItem(LAST_ROUTE_KEY);
    setUser(null);
    localStorage.removeItem('carbot_session');
    if (window.location.pathname !== '/login') {
      window.history.pushState({}, '', '/login');
    }
    setCurrentRoute('/login');
  };

  const handleIrAMecanicos = () => {
    setGestionSubTab('mecanicos');
    navigate('/gestion');
  };

  const handleIrAFallas = () => {
    setGestionSubTab('historial');
    navigate('/gestion');
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
            minWidth: 0,
            padding: '24px 32px',
            width: '100%',
            maxWidth: '100%',
          }}
          className="app-main-content"
        >
          {activeTab === 'inicio' && (
            <DashboardView
              onIrAFallas={handleIrAFallas}
              onIrAMecanicos={handleIrAMecanicos}
            />
          )}


          {activeTab === 'gestion' && (
            <GestionChatbotView
              initialSubTab={gestionSubTab}
              solicitudes={solicitudes}
              cargandoSolicitudes={cargandoSolicitudes}
              mecanicos={mecanicos}
              cargandoMecanicos={cargandoMecanicos}
              diagnosticos={diagnosticos}
              totalDiagnosticos={totalDiagnosticos}
              cargandoDiagnosticos={cargandoDiagnosticos}
              errorSolicitudes={errorSolicitudes}
              errorMecanicos={errorMecanicos}
              errorDiagnosticos={errorDiagnosticos}
              onRecargarSolicitudes={cargarSolicitudes}
              onRecargarMecanicos={cargarMecanicos}
              onFiltrarDiagnosticos={cargarDiagnosticos}
              diagnosticoSeleccionadoModal={diagnosticoSeleccionado}
              onCerrarModalDetalle={() => setDiagnosticoSeleccionado(null)}
              onAbrirModalDetalle={(diag) => setDiagnosticoSeleccionado(diag)}
            />
          )}

          {activeTab === 'proyecto' && (
            <ProyectoCarbotView />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
