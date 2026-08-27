import React, { useState, useEffect, useCallback } from 'react';
import {
  Inbox,
  Wrench,
  FileSearch,
  RefreshCw,
  SlidersHorizontal,
  Users,
} from 'lucide-react';
import type {
  Cliente,
  Diagnostico,
  EstadoDiagnostico,
  Mecanico,
  SolicitudAcceso,
  UsuarioSesion,
} from '../../types';
import { apiService } from '../../services/api';
import { SolicitudesTab } from './personas/SolicitudesTab';
import { MecanicosAutorizadosTab } from './gestion/MecanicosAutorizadosTab';
import { ClientesTab } from './personas/ClientesTab';
import { DiagnosticosView } from './DiagnosticosView';

export type GestionSubTab = 'solicitudes' | 'mecanicos' | 'clientes' | 'historial';

export interface GestionChatbotViewProps {
  user: UsuarioSesion | null;
  initialSubTab?: GestionSubTab;
  solicitudes: SolicitudAcceso[];
  cargandoSolicitudes: boolean;
  mecanicos: Mecanico[];
  cargandoMecanicos: boolean;
  diagnosticos: Diagnostico[];
  cargandoDiagnosticos: boolean;
  onRecargarDatos: () => void;
  onActualizarEstadoDiagnostico: (id: string, nuevoEstado: EstadoDiagnostico, notas?: string) => Promise<void>;
  onFiltrarDiagnosticos?: (filtros: { busqueda?: string; estado?: string; modo?: string; mecanico_id?: string }) => Promise<void>;
  diagnosticoSeleccionadoModal?: Diagnostico | null;
  onCerrarModalDetalle: () => void;
  onAbrirModalDetalle: (diag: Diagnostico) => void;
}

export const GestionChatbotView: React.FC<GestionChatbotViewProps> = ({
  user,
  initialSubTab = 'solicitudes',
  solicitudes,
  cargandoSolicitudes,
  mecanicos,
  cargandoMecanicos,
  diagnosticos,
  cargandoDiagnosticos,
  onRecargarDatos,
  onActualizarEstadoDiagnostico,
  onFiltrarDiagnosticos,
  diagnosticoSeleccionadoModal,
  onCerrarModalDetalle,
  onAbrirModalDetalle,
}) => {
  const [subTab, setSubTab] = useState<GestionSubTab>(initialSubTab);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [cargandoClientes, setCargandoClientes] = useState(false);

  // Synchronize when initialSubTab prop changes
  useEffect(() => {
    if (initialSubTab) {
      setSubTab(initialSubTab);
    }
  }, [initialSubTab]);

  const cargarClientes = useCallback(async () => {
    try {
      setCargandoClientes(true);
      const lista = await apiService.getClientes();
      setClientes(Array.isArray(lista) ? lista : []);
    } catch (err) {
      console.error('Error al cargar clientes:', err);
    } finally {
      setCargandoClientes(false);
    }
  }, []);

  useEffect(() => {
    cargarClientes();
  }, [cargarClientes]);

  const handleRecargarTodo = useCallback(async () => {
    await Promise.all([onRecargarDatos(), cargarClientes()]);
  }, [onRecargarDatos, cargarClientes]);

  const solicitudesPendientes = solicitudes.filter((s) => s.estado === 'pendiente').length;
  const totalMecanicos = mecanicos.length;
  const totalClientes = clientes.length;

  const handleVerConsultasDeMecanico = useCallback((mecanicoId: string) => {
    setSubTab('historial');
    if (onFiltrarDiagnosticos) {
      onFiltrarDiagnosticos({ mecanico_id: mecanicoId });
    }
  }, [onFiltrarDiagnosticos]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header with Title and Global Refresh */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <SlidersHorizontal size={20} style={{ color: 'var(--primary)' }} />
            <h1 style={{ fontSize: '19px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
              Personas y Diagnósticos
            </h1>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '3px 0 0 0' }}>
            Gestión integral de accesos, clientes WhatsApp, equipo de mecánicos e historial clínico de diagnósticos.
          </p>
        </div>

        <button
          type="button"
          onClick={handleRecargarTodo}
          disabled={cargandoSolicitudes || cargandoMecanicos || cargandoDiagnosticos || cargandoClientes}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            color: 'var(--text-secondary)',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          }}
        >
          <RefreshCw
            size={14}
            className={cargandoSolicitudes || cargandoMecanicos || cargandoDiagnosticos || cargandoClientes ? 'animate-spin' : ''}
          />
          <span>Actualizar</span>
        </button>
      </div>

      {/* 4-Tab Segmented Switcher */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          backgroundColor: '#f1f5f9',
          padding: '4px',
          borderRadius: '10px',
          gap: '4px',
        }}
      >
        <button
          type="button"
          onClick={() => setSubTab('solicitudes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'solicitudes' ? '#ffffff' : 'transparent',
            color: subTab === 'solicitudes' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'solicitudes' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            position: 'relative',
          }}
        >
          <Inbox size={15} />
          <span>Solicitudes</span>
          {solicitudesPendientes > 0 && (
            <span
              style={{
                backgroundColor: '#ef4444',
                color: '#ffffff',
                fontSize: '10px',
                fontWeight: 800,
                borderRadius: '9999px',
                padding: '1px 6px',
                marginLeft: '4px',
              }}
            >
              {solicitudesPendientes}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setSubTab('mecanicos')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'mecanicos' ? '#ffffff' : 'transparent',
            color: subTab === 'mecanicos' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'mecanicos' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
          }}
        >
          <Wrench size={15} />
          <span>Mecánicos</span>
          <span
            style={{
              backgroundColor: subTab === 'mecanicos' ? 'var(--primary-light)' : '#e2e8f0',
              color: subTab === 'mecanicos' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '10px',
              fontWeight: 700,
              borderRadius: '9999px',
              padding: '1px 6px',
              marginLeft: '4px',
            }}
          >
            {totalMecanicos}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setSubTab('clientes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'clientes' ? '#ffffff' : 'transparent',
            color: subTab === 'clientes' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'clientes' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
          }}
        >
          <Users size={15} />
          <span>Clientes</span>
          <span
            style={{
              backgroundColor: subTab === 'clientes' ? 'var(--primary-light)' : '#e2e8f0',
              color: subTab === 'clientes' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '10px',
              fontWeight: 700,
              borderRadius: '9999px',
              padding: '1px 6px',
              marginLeft: '4px',
            }}
          >
            {totalClientes}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setSubTab('historial')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'historial' ? '#ffffff' : 'transparent',
            color: subTab === 'historial' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'historial' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
          }}
        >
          <FileSearch size={15} />
          <span>Historial Diagnósticos</span>
        </button>
      </div>

      {/* Subtab 1: Solicitudes Pendientes */}
      {subTab === 'solicitudes' && (
        <SolicitudesTab
          solicitudes={solicitudes}
          cargando={cargandoSolicitudes}
          onRecargar={handleRecargarTodo}
        />
      )}

      {/* Subtab 2: Mecánicos Autorizados */}
      {subTab === 'mecanicos' && (
        <MecanicosAutorizadosTab
          mecanicos={mecanicos}
          cargando={cargandoMecanicos}
          onRecargar={handleRecargarTodo}
          onVerConsultasMecanico={handleVerConsultasDeMecanico}
        />
      )}

      {/* Subtab 3: Clientes Registrados */}
      {subTab === 'clientes' && (
        <ClientesTab
          clientes={clientes}
          cargando={cargandoClientes}
          onRecargar={handleRecargarTodo}
        />
      )}

      {/* Subtab 4: Historial de Diagnósticos */}
      {subTab === 'historial' && (
        <DiagnosticosView
          diagnosticos={diagnosticos}
          cargando={cargandoDiagnosticos}
          mecanicos={mecanicos}
          currentUser={user}
          onActualizarEstado={onActualizarEstadoDiagnostico}
          onFiltrar={onFiltrarDiagnosticos}
          diagnosticoSeleccionadoModal={diagnosticoSeleccionadoModal}
          onCerrarModalDetalle={onCerrarModalDetalle}
          onAbrirModalDetalle={onAbrirModalDetalle}
        />
      )}
    </div>
  );
};
