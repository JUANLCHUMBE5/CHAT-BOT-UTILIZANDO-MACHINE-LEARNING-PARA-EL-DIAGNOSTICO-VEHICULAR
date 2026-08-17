import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  Wrench,
  RefreshCw,
  MessageSquare
} from 'lucide-react';
import type { Cliente, SolicitudAcceso, Mecanico, UsuarioSesion } from '../../types';
import { getErrorMessage } from '../../utils/errors';
import { apiService } from '../../services/api';
import { SolicitudesTab } from './personas/SolicitudesTab';
import { ClientesTab } from './personas/ClientesTab';
import { EquipoTallerTab } from './personas/EquipoTallerTab';

export interface PersonasAccesosViewProps {
  user: UsuarioSesion | null;
  initialTab?: 'solicitudes' | 'clientes' | 'equipo';
  onRecargarMecanicos?: () => void;
  onActualizarPerfilSesion?: (actualizado: Partial<UsuarioSesion>) => void;
}

export const PersonasAccesosView: React.FC<PersonasAccesosViewProps> = ({
  user,
  initialTab = 'solicitudes',
  onRecargarMecanicos,
  onActualizarPerfilSesion,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'solicitudes' | 'clientes' | 'equipo'>(initialTab);
  const [solicitudes, setSolicitudes] = useState<SolicitudAcceso[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [mecanicos, setMecanicos] = useState<Mecanico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarTodosLosDatos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [listaSol, listaCli, listaMec] = await Promise.all([
        apiService.getSolicitudesAcceso(),
        apiService.getClientes(),
        apiService.getMecanicos(),
      ]);
      setSolicitudes(listaSol);
      setClientes(listaCli);
      setMecanicos(listaMec);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Error al cargar datos de personas y accesos'));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarTodosLosDatos();
  }, [cargarTodosLosDatos]);

  const handleAccionCompletada = useCallback(async () => {
    await cargarTodosLosDatos();
    if (onRecargarMecanicos) {
      onRecargarMecanicos();
    }
  }, [cargarTodosLosDatos, onRecargarMecanicos]);

  const pendientesCount = solicitudes.filter((s) => s.estado === 'pendiente').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* View Header (Limpio y compacto en 1 sola línea) */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '19px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Personas y Accesos
          </h1>
          <p className="desktop-only" style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Directorio de clientes, solicitudes de ingreso y equipo del taller.
          </p>
        </div>

        <button
          type="button"
          onClick={cargarTodosLosDatos}
          disabled={cargando}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '12px',
            fontWeight: 500,
            cursor: 'pointer',
            color: 'var(--text-secondary)',
            flexShrink: 0,
          }}
        >
          <RefreshCw size={13} className={cargando ? 'animate-spin' : ''} />
          <span className="desktop-only">Actualizar Datos</span>
          <span className="mobile-only">Actualizar</span>
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#ef4444',
            fontSize: '13px',
          }}
        >
          {error}
        </div>
      )}

      {/* Overview Stat Cards (3 en 1 sola fila responsiva) */}
      <div className="personas-stat-grid">
        <div
          className={`personas-stat-card ${activeSubTab === 'solicitudes' ? 'active-tab' : ''}`}
          onClick={() => setActiveSubTab('solicitudes')}
        >
          <div
            className="personas-stat-icon"
            style={{
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              color: '#3b82f6',
            }}
          >
            <Clock size={20} />
          </div>
          <div className="personas-stat-info">
            <div className="personas-stat-label">
              <span className="desktop-only">Solicitudes Pendientes</span>
              <span className="mobile-only">Solicitudes</span>
            </div>
            <div className="personas-stat-value">
              {pendientesCount}
            </div>
          </div>
        </div>

        <div
          className={`personas-stat-card ${activeSubTab === 'clientes' ? 'active-tab' : ''}`}
          onClick={() => setActiveSubTab('clientes')}
        >
          <div
            className="personas-stat-icon"
            style={{
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              color: '#10b981',
            }}
          >
            <MessageSquare size={20} />
          </div>
          <div className="personas-stat-info">
            <div className="personas-stat-label">
              <span className="desktop-only">Clientes Registrados</span>
              <span className="mobile-only">Clientes</span>
            </div>
            <div className="personas-stat-value">
              {clientes.length}
            </div>
          </div>
        </div>

        <div
          className={`personas-stat-card ${activeSubTab === 'equipo' ? 'active-tab' : ''}`}
          onClick={() => setActiveSubTab('equipo')}
        >
          <div
            className="personas-stat-icon"
            style={{
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              color: '#6366f1',
            }}
          >
            <Wrench size={20} />
          </div>
          <div className="personas-stat-info">
            <div className="personas-stat-label">
              <span className="desktop-only">Equipo del Taller</span>
              <span className="mobile-only">Equipo</span>
            </div>
            <div className="personas-stat-value">
              {mecanicos.length}
            </div>
          </div>
        </div>
      </div>

      {/* Active Sub-Tab View Content */}
      <div style={{ marginTop: '8px' }}>
        {activeSubTab === 'solicitudes' && (
          <SolicitudesTab
            solicitudes={solicitudes}
            cargando={cargando}
            onRecargar={handleAccionCompletada}
          />
        )}

        {activeSubTab === 'clientes' && (
          <ClientesTab
            clientes={clientes}
            cargando={cargando}
            onRecargar={handleAccionCompletada}
          />
        )}

        {activeSubTab === 'equipo' && (
          <EquipoTallerTab
            mecanicos={mecanicos}
            cargando={cargando}
            currentUser={user}
            onRecargar={handleAccionCompletada}
            onActualizarPerfilSesion={onActualizarPerfilSesion}
          />
        )}
      </div>
    </div>
  );
};
