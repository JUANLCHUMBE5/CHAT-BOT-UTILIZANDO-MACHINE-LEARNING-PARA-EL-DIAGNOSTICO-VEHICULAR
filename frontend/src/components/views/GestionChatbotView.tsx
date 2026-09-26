import React, { useState, useEffect, useCallback } from 'react';
import {
  FileSearch,
  RefreshCw,
  SlidersHorizontal,
  Users,
  Wrench,
} from 'lucide-react';
import type {
  Cliente,
  Diagnostico,
  Mecanico,
  SolicitudAcceso,
} from '../../types';
import { apiService } from '../../services/api';
import { MecanicosAutorizadosTab } from './gestion/MecanicosAutorizadosTab';
import { DiagnosticosView } from './DiagnosticosView';
import { AccesosView } from './accesos/AccesosView';

export type GestionSubTab =
  | 'diagnosticos'
  | 'mecanicos'
  | 'accesos'
  | 'solicitudes'
  | 'clientes'
  | 'historial';

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

const normalizarSubTab = (tab?: GestionSubTab): 'diagnosticos' | 'mecanicos' | 'accesos' => {
  if (tab === 'historial' || tab === 'diagnosticos') return 'diagnosticos';
  if (tab === 'mecanicos') return 'mecanicos';
  if (tab === 'solicitudes' || tab === 'clientes' || tab === 'accesos') return 'accesos';
  return 'diagnosticos';
};

export const GestionChatbotView: React.FC<GestionChatbotViewProps> = ({
  initialSubTab = 'diagnosticos',
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
  const [subTab, setSubTab] = useState<'diagnosticos' | 'mecanicos' | 'accesos'>(
    normalizarSubTab(initialSubTab)
  );
  const [filtroMecanicoId, setFiltroMecanicoId] = useState<string>('todos');
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [clientesCargados, setClientesCargados] = useState(false);
  const [cargandoClientes, setCargandoClientes] = useState(false);
  const [errorCargaClientes, setErrorCargaClientes] = useState<string | null>(null);
  const [recargaHistorial, setRecargaHistorial] = useState(0);

  // Sincronizar subtab si cambia la propiedad inicial
  useEffect(() => {
    if (initialSubTab) {
      setSubTab(normalizarSubTab(initialSubTab));
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
      const msg = err instanceof Error ? err.message : 'Error al cargar usuarios de WhatsApp';
      setErrorCargaClientes(msg);
      console.error('Error al cargar contactos:', err);
    } finally {
      setCargandoClientes(false);
    }
  }, []);

  // Carga diferida de contactos al abrir la pestaña de Accesos
  useEffect(() => {
    if (subTab === 'accesos' && !clientesCargados && !cargandoClientes) {
      cargarClientes();
    }
  }, [subTab, clientesCargados, cargandoClientes, cargarClientes]);

  const handleRecargarTodo = useCallback(async () => {
    if (subTab === 'accesos') {
      await Promise.allSettled([onRecargarSolicitudes(), cargarClientes()]);
    } else if (subTab === 'mecanicos') {
      await onRecargarMecanicos();
    } else {
      setRecargaHistorial((valor) => valor + 1);
    }
  }, [subTab, onRecargarSolicitudes, onRecargarMecanicos, cargarClientes]);

  const solicitudesPendientes = solicitudes.filter((s) => s.estado === 'pendiente').length;
  const totalMecanicos = mecanicos.filter((m) => m.activo && !m.bloqueado).length;

  const handleVerConsultasDeMecanico = useCallback((mecanicoId: string) => {
    setFiltroMecanicoId(mecanicoId);
    setSubTab('diagnosticos');
  }, []);

  const handleVerHistorialDeUsuario = useCallback((cliente: Cliente) => {
    setSubTab('diagnosticos');
    if (onFiltrarDiagnosticos) {
      void onFiltrarDiagnosticos({
        busqueda: cliente.telefono || cliente.nombres || undefined,
        limite: 10,
        offset: 0,
      });
    }
  }, [onFiltrarDiagnosticos]);

  const errorActivo =
    subTab === 'accesos'
      ? errorSolicitudes || errorCargaClientes
      : subTab === 'mecanicos'
        ? errorMecanicos
        : errorDiagnosticos;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Cabecera con Título del Módulo y Botón de Actualizar */}
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
            className={
              cargandoSolicitudes || cargandoMecanicos || cargandoDiagnosticos || cargandoClientes
                ? 'animate-spin'
                : ''
            }
          />
          <span>Actualizar</span>
        </button>
      </div>

      {errorActivo && (
        <div className="inline-error" role="alert">
          {errorActivo}
        </div>
      )}

      {/* Selector de 3 Pestañas Principales: Diagnósticos (Default) | Mecánicos | Accesos */}
      <div className="gestion-subtabs-grid">
        {/* 1. Diagnósticos (Predeterminado) */}
        <button
          type="button"
          onClick={() => {
            setFiltroMecanicoId('todos');
            setSubTab('diagnosticos');
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
            backgroundColor: subTab === 'diagnosticos' ? '#ffffff' : 'transparent',
            color: subTab === 'diagnosticos' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'diagnosticos' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <FileSearch size={14} />
          <span>Diagnósticos</span>
          <span
            style={{
              backgroundColor: subTab === 'diagnosticos' ? 'var(--primary-light)' : '#e2e8f0',
              color: subTab === 'diagnosticos' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '9.5px',
              fontWeight: 700,
              borderRadius: '9999px',
              padding: '1px 6px',
            }}
          >
            {totalDiagnosticos}
          </span>
        </button>

        {/* 2. Mecánicos */}
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

        {/* 3. Accesos (Pendientes, Historial, Usuarios WhatsApp) */}
        <button
          type="button"
          onClick={() => setSubTab('accesos')}
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
            backgroundColor: subTab === 'accesos' ? '#ffffff' : 'transparent',
            color: subTab === 'accesos' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'accesos' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <Users size={14} />
          <span>Accesos</span>
          {solicitudesPendientes > 0 ? (
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
          ) : (
            <span
              style={{
                backgroundColor: subTab === 'accesos' ? 'var(--primary-light)' : '#e2e8f0',
                color: subTab === 'accesos' ? 'var(--primary)' : 'var(--text-muted)',
                fontSize: '9.5px',
                fontWeight: 700,
                borderRadius: '9999px',
                padding: '1px 6px',
              }}
            >
              {solicitudes.length}
            </span>
          )}
        </button>
      </div>

      {/* PESTAÑA 1: DIAGNÓSTICOS (PREDETERMINADA) */}
      {subTab === 'diagnosticos' && (
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

      {/* PESTAÑA 2: MECÁNICOS AUTORIZADOS */}
      {subTab === 'mecanicos' && (
        <MecanicosAutorizadosTab
          mecanicos={mecanicos}
          cargando={cargandoMecanicos}
          onRecargar={onRecargarMecanicos}
          onVerConsultasMecanico={handleVerConsultasDeMecanico}
        />
      )}

      {/* PESTAÑA 3: ACCESOS (PENDIENTES, HISTORIAL, USUARIOS WHATSAPP) */}
      {subTab === 'accesos' && (
        <AccesosView
          solicitudes={solicitudes}
          cargandoSolicitudes={cargandoSolicitudes}
          onRecargarSolicitudes={onRecargarSolicitudes}
          clientes={clientes}
          cargandoClientes={cargandoClientes}
          onRecargarClientes={cargarClientes}
          onVerHistorialDiagnosticos={handleVerHistorialDeUsuario}
        />
      )}
    </div>
  );
};
