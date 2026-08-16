import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
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
}

export const PersonasAccesosView: React.FC<PersonasAccesosViewProps> = ({
  user,
  initialTab = 'solicitudes',
  onRecargarMecanicos,
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* View Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Personas y Accesos
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Consolidado de solicitudes de ingreso, directorio de clientes y administración del equipo técnico.
          </p>
        </div>

        <button
          type="button"
          onClick={cargarTodosLosDatos}
          disabled={cargando}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 14px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '13px',
            fontWeight: 500,
            cursor: 'pointer',
            color: 'var(--text-secondary)',
          }}
        >
          <RefreshCw size={14} className={cargando ? 'animate-spin' : ''} />
          <span>Actualizar Datos</span>
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

      {/* Overview Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div
          style={{
            padding: '18px',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            cursor: 'pointer',
            borderColor: activeSubTab === 'solicitudes' ? '#3b82f6' : 'var(--border-color)',
          }}
          onClick={() => setActiveSubTab('solicitudes')}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#3b82f6',
            }}
          >
            <Clock size={22} />
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Solicitudes Pendientes
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              {pendientesCount}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '18px',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            cursor: 'pointer',
            borderColor: activeSubTab === 'clientes' ? '#3b82f6' : 'var(--border-color)',
          }}
          onClick={() => setActiveSubTab('clientes')}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#10b981',
            }}
          >
            <MessageSquare size={22} />
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Clientes Registrados
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              {clientes.length}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '18px',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            cursor: 'pointer',
            borderColor: activeSubTab === 'equipo' ? '#3b82f6' : 'var(--border-color)',
          }}
          onClick={() => setActiveSubTab('equipo')}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6366f1',
            }}
          >
            <Wrench size={22} />
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Equipo del Taller
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              {mecanicos.length}
            </div>
          </div>
        </div>
      </div>

      {/* Main Tab Navigation Bar */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '2px solid var(--border-color)', paddingBottom: '0px' }}>
        <button
          type="button"
          onClick={() => setActiveSubTab('solicitudes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            border: 'none',
            borderBottom: activeSubTab === 'solicitudes' ? '3px solid #3b82f6' : '3px solid transparent',
            backgroundColor: 'transparent',
            color: activeSubTab === 'solicitudes' ? '#3b82f6' : 'var(--text-secondary)',
            marginBottom: '-2px',
            transition: 'all 0.2s ease',
          }}
        >
          <Clock size={18} />
          <span>Solicitudes de Acceso</span>
          {pendientesCount > 0 && (
            <span
              style={{
                padding: '2px 8px',
                borderRadius: '12px',
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: activeSubTab === 'solicitudes' ? '#3b82f6' : 'rgba(245, 158, 11, 0.2)',
                color: activeSubTab === 'solicitudes' ? '#ffffff' : '#b45309',
              }}
            >
              {pendientesCount}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab('clientes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            border: 'none',
            borderBottom: activeSubTab === 'clientes' ? '3px solid #3b82f6' : '3px solid transparent',
            backgroundColor: 'transparent',
            color: activeSubTab === 'clientes' ? '#3b82f6' : 'var(--text-secondary)',
            marginBottom: '-2px',
            transition: 'all 0.2s ease',
          }}
        >
          <Users size={18} />
          <span>Directorio de Clientes</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab('equipo')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            border: 'none',
            borderBottom: activeSubTab === 'equipo' ? '3px solid #3b82f6' : '3px solid transparent',
            backgroundColor: 'transparent',
            color: activeSubTab === 'equipo' ? '#3b82f6' : 'var(--text-secondary)',
            marginBottom: '-2px',
            transition: 'all 0.2s ease',
          }}
        >
          <Wrench size={18} />
          <span>Equipo del Taller</span>
        </button>
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
          />
        )}
      </div>
    </div>
  );
};
