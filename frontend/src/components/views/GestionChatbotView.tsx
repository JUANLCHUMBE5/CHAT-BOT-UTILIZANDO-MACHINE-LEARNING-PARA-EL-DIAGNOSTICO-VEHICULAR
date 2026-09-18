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
  Mecanico,
  SolicitudAcceso,
} from '../../types';
import { apiService } from '../../services/api';
import { SolicitudesTab } from './personas/SolicitudesTab';
import { MecanicosAutorizadosTab } from './gestion/MecanicosAutorizadosTab';
import { ClientesTab } from './personas/ClientesTab';
import { DiagnosticosView } from './DiagnosticosView';

export type GestionSubTab = 'solicitudes' | 'mecanicos' | 'clientes' | 'historial';

export interface GestionChatbotViewProps {
  initialSubTab?: GestionSubTab;
  solicitudes: SolicitudAcceso[];
  cargandoSolicitudes: boolean;
  mecanicos: Mecanico[];
  cargandoMecanicos: boolean;
  diagnosticos: Diagnostico[];
  totalDiagnosticos: number;
  cargandoDiagnosticos: boolean;
  errorSolicitudes?: string | null;
  errorMecanicos?: string | null;
  errorDiagnosticos?: string | null;
  onRecargarSolicitudes: () => void | Promise<void>;
  onRecargarMecanicos: () => void | Promise<void>;
  onFiltrarDiagnosticos?: (filtros: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
    limite?: number;
    offset?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }) => Promise<void>;
  diagnosticoSeleccionadoModal?: Diagnostico | null;
  onCerrarModalDetalle: () => void;
  onAbrirModalDetalle: (diag: Diagnostico) => void;
}

export const GestionChatbotView: React.FC<GestionChatbotViewProps> = ({
  initialSubTab = 'solicitudes',
  solicitudes,
  cargandoSolicitudes,
  mecanicos,
  cargandoMecanicos,
  diagnosticos,
  totalDiagnosticos,
  cargandoDiagnosticos,
  errorSolicitudes,
  errorMecanicos,
  errorDiagnosticos,
  onRecargarSolicitudes,
  onRecargarMecanicos,
  onFiltrarDiagnosticos,
  diagnosticoSeleccionadoModal,
  onCerrarModalDetalle,
  onAbrirModalDetalle,
}) => {
  const [subTab, setSubTab] = useState<GestionSubTab>(initialSubTab);
  const [filtroMecanicoId, setFiltroMecanicoId] = useState<string>('todos');
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [clientesCargados, setClientesCargados] = useState(false);
  const [cargandoClientes, setCargandoClientes] = useState(false);
  const [errorCargaClientes, setErrorCargaClientes] = useState<string | null>(null);
  const [recargaHistorial, setRecargaHistorial] = useState(0);

  // Synchronize when initialSubTab prop changes
  useEffect(() => {
    if (initialSubTab) {
      setSubTab(initialSubTab);
    }
  }, [initialSubTab]);

  const cargarClientes = useCallback(async () => {
    try {
      setCargandoClientes(true);
      setErrorCargaClientes(null);
      const lista = await apiService.getClientes();
      setClientes(Array.isArray(lista) ? lista : []);
      setClientesCargados(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al cargar contactos';
      setErrorCargaClientes(msg);
      console.error('Error al cargar contactos:', err);
    } finally {
      setCargandoClientes(false);
    }
  }, []);

  // Carga perezosa de contactos solo cuando se ingresa a la pestaña de contactos
  useEffect(() => {
    if (subTab === 'clientes' && !clientesCargados && !cargandoClientes) {
      cargarClientes();
    }
  }, [subTab, clientesCargados, cargandoClientes, cargarClientes]);

  const handleRecargarTodo = useCallback(async () => {
    if (subTab === 'clientes') {
      await cargarClientes();
    } else if (subTab === 'solicitudes') {
      await onRecargarSolicitudes();
    } else if (subTab === 'mecanicos') {
      await onRecargarMecanicos();
    } else {
      setRecargaHistorial((valor) => valor + 1);
    }
  }, [subTab, onRecargarSolicitudes, onRecargarMecanicos, cargarClientes]);

  const solicitudesPendientes = solicitudes.filter((s) => s.estado === 'pendiente').length;
  const totalMecanicos = mecanicos.filter((m) => m.activo && !m.bloqueado).length;
  const totalClientes = clientes.length;

  const handleVerConsultasDeMecanico = useCallback((mecanicoId: string) => {
    setFiltroMecanicoId(mecanicoId);
    setSubTab('historial');
  }, []);

  const errorActivo = subTab === 'solicitudes'
    ? errorSolicitudes
    : subTab === 'mecanicos'
      ? errorMecanicos
      : subTab === 'historial'
        ? errorDiagnosticos
        : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header with Title and Global Refresh */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <SlidersHorizontal size={18} style={{ color: 'var(--primary)' }} />
          <h1 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Accesos y Diagnósticos
          </h1>
        </div>

        <button
          type="button"
          onClick={handleRecargarTodo}
          disabled={cargandoSolicitudes || cargandoMecanicos || cargandoDiagnosticos || cargandoClientes}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '5px 10px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            cursor: 'pointer',
            color: 'var(--text-secondary)',
          }}
        >
          <RefreshCw
            size={13}
            className={cargandoSolicitudes || cargandoMecanicos || cargandoDiagnosticos || cargandoClientes ? 'animate-spin' : ''}
          />
          <span>Actualizar</span>
        </button>
      </div>

      {errorActivo && (
        <div className="inline-error" role="alert">
          {errorActivo}
        </div>
      )}

      {/* 4-Tab Segmented Switcher (2x2 en móvil, 4 columnas en desktop) */}
      <div className="gestion-subtabs-grid">
        <button
          type="button"
          onClick={() => setSubTab('solicitudes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '8px 10px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'solicitudes' ? '#ffffff' : 'transparent',
            color: subTab === 'solicitudes' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'solicitudes' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <Inbox size={14} />
          <span>Solicitudes</span>
          {solicitudesPendientes > 0 && (
            <span
              style={{
                backgroundColor: '#ef4444',
                color: '#ffffff',
                fontSize: '9.5px',
                fontWeight: 800,
                borderRadius: '9999px',
                padding: '1px 6px',
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
            gap: '6px',
            padding: '8px 10px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'mecanicos' ? '#ffffff' : 'transparent',
            color: subTab === 'mecanicos' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'mecanicos' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <Wrench size={14} />
          <span>Mecánicos</span>
          <span
            style={{
              backgroundColor: subTab === 'mecanicos' ? 'var(--primary-light)' : '#e2e8f0',
              color: subTab === 'mecanicos' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '9.5px',
              fontWeight: 700,
              borderRadius: '9999px',
              padding: '1px 6px',
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
            gap: '6px',
            padding: '8px 10px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'clientes' ? '#ffffff' : 'transparent',
            color: subTab === 'clientes' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'clientes' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <Users size={14} />
          <span>Contactos</span>
          <span
            style={{
              backgroundColor: subTab === 'clientes' ? 'var(--primary-light)' : '#e2e8f0',
              color: subTab === 'clientes' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '9.5px',
              fontWeight: 700,
              borderRadius: '9999px',
              padding: '1px 6px',
            }}
          >
            {totalClientes}
          </span>
        </button>

        <button
          type="button"
          onClick={() => {
            setFiltroMecanicoId('todos');
            setSubTab('historial');
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '8px 10px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'historial' ? '#ffffff' : 'transparent',
            color: subTab === 'historial' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'historial' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <FileSearch size={14} />
          <span>Diagnósticos</span>
          <span
            style={{
              backgroundColor: subTab === 'historial' ? 'var(--primary-light)' : '#e2e8f0',
              color: subTab === 'historial' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '9.5px',
              fontWeight: 700,
              borderRadius: '9999px',
              padding: '1px 6px',
            }}
          >
            {totalDiagnosticos}
          </span>
        </button>
      </div>

      {/* Subtab 1: Solicitudes Pendientes */}
      {subTab === 'solicitudes' && (
        <SolicitudesTab
          solicitudes={solicitudes}
          cargando={cargandoSolicitudes}
          onRecargar={onRecargarSolicitudes}
        />
      )}

      {/* Subtab 2: Mecánicos Autorizados */}
      {subTab === 'mecanicos' && (
        <MecanicosAutorizadosTab
          mecanicos={mecanicos}
          cargando={cargandoMecanicos}
          onRecargar={onRecargarMecanicos}
          onVerConsultasMecanico={handleVerConsultasDeMecanico}
        />
      )}

      {/* Subtab 3: Contactos / Propietarios */}
      {subTab === 'clientes' && (
        <>
          {errorCargaClientes && (
            <div
              style={{
                backgroundColor: '#fef2f2',
                color: '#991b1b',
                border: '1px solid #fecaca',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>{errorCargaClientes}</span>
              <button
                type="button"
                onClick={cargarClientes}
                style={{ background: 'none', border: 'none', color: '#991b1b', fontWeight: 700, cursor: 'pointer', fontSize: '11px' }}
              >
                Reintentar
              </button>
            </div>
          )}
          <ClientesTab
            clientes={clientes}
            cargando={cargandoClientes}
            onRecargar={cargarClientes}
          />
        </>
      )}

      {/* Subtab 4: Historial de Diagnósticos */}
      {subTab === 'historial' && (
        <DiagnosticosView
          diagnosticos={diagnosticos}
          totalDiagnosticos={totalDiagnosticos}
          cargando={cargandoDiagnosticos}
          mecanicos={mecanicos}
          initialFiltroMecanico={filtroMecanicoId}
          onFiltroMecanicoSeleccionado={setFiltroMecanicoId}
          onFiltrar={onFiltrarDiagnosticos}
          error={null}
          refreshKey={recargaHistorial}
          diagnosticoSeleccionadoModal={diagnosticoSeleccionadoModal}
          onCerrarModalDetalle={onCerrarModalDetalle}
          onAbrirModalDetalle={onAbrirModalDetalle}
        />
      )}
    </div>
  );
};
