import React, { useState } from 'react';
import { Clock, History, MessageSquare, AlertTriangle } from 'lucide-react';
import type { Cliente, SolicitudAcceso } from '../../../types';
import { useSolicitudesActions } from '../../../hooks/useSolicitudesActions';
import {
  SolicitudesPendientesTable,
  SolicitudesHistorialTable,
  SolicitudesModals,
} from '../personas/solicitudes';
import { ClientesTab } from '../personas/ClientesTab';

export type AccesosSubTab = 'pendientes' | 'historial' | 'usuarios';

export interface AccesosViewProps {
  solicitudes: SolicitudAcceso[];
  cargandoSolicitudes: boolean;
  onRecargarSolicitudes: () => void | Promise<void>;
  clientes: Cliente[];
  cargandoClientes: boolean;
  onRecargarClientes: () => void | Promise<void>;
  onVerHistorialDiagnosticos?: (cliente: Cliente) => void;
  initialSubTab?: AccesosSubTab;
}

export const AccesosView: React.FC<AccesosViewProps> = ({
  solicitudes,
  cargandoSolicitudes,
  onRecargarSolicitudes,
  clientes,
  cargandoClientes,
  onRecargarClientes,
  onVerHistorialDiagnosticos,
  initialSubTab = 'pendientes',
}) => {
  const [subTab, setSubTab] = useState<AccesosSubTab>(initialSubTab);

  const {
    modalAprobado,
    setModalAprobado,
    aprobandoId,
    modalRechazo,
    setModalRechazo,
    motivoRechazo,
    setMotivoRechazo,
    rechazando,
    errorRechazo,
    notificacionError,
    setNotificacionError,
    handleAprobarSolicitud,
    handleAbrirModalRechazo,
    handleConfirmarRechazo,
  } = useSolicitudesActions({ onRecargar: onRecargarSolicitudes });

  const pendientes = solicitudes.filter((s) => s.estado === 'pendiente');
  const historial = solicitudes.filter((s) => s.estado !== 'pendiente');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Banner de error de solicitudes */}
      {notificacionError && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 14px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#b91c1c',
            fontSize: '12px',
          }}
        >
          <AlertTriangle size={16} style={{ flexShrink: 0 }} />
          <span style={{ flex: 1 }}>{notificacionError}</span>
          <button
            type="button"
            onClick={() => setNotificacionError(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b91c1c', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Subpestañas Accesos: [Pendientes (N)] [Historial] [Usuarios WhatsApp] */}
      <div
        style={{
          display: 'flex',
          gap: '6px',
          backgroundColor: '#ffffff',
          padding: '6px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <button
          type="button"
          onClick={() => setSubTab('pendientes')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 12px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            backgroundColor: subTab === 'pendientes' ? 'var(--primary)' : 'transparent',
            color: subTab === 'pendientes' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <Clock size={14} />
          <span>Pendientes</span>
          {pendientes.length > 0 && (
            <span
              style={{
                padding: '1px 6px',
                borderRadius: '10px',
                fontSize: '10px',
                fontWeight: 800,
                backgroundColor: subTab === 'pendientes' ? 'rgba(255, 255, 255, 0.3)' : '#ef4444',
                color: '#ffffff',
              }}
            >
              {pendientes.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setSubTab('historial')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 12px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            backgroundColor: subTab === 'historial' ? 'var(--primary)' : 'transparent',
            color: subTab === 'historial' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <History size={14} />
          <span>Historial ({historial.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setSubTab('usuarios')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 12px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            backgroundColor: subTab === 'usuarios' ? 'var(--primary)' : 'transparent',
            color: subTab === 'usuarios' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <MessageSquare size={14} />
          <span>Usuarios WhatsApp ({clientes.length})</span>
        </button>
      </div>

      {/* Contenido según subpestaña */}
      {subTab === 'pendientes' && (
        <SolicitudesPendientesTable
          pendientes={pendientes}
          aprobandoId={aprobandoId}
          cargando={cargandoSolicitudes}
          onAprobar={handleAprobarSolicitud}
          onRechazar={handleAbrirModalRechazo}
        />
      )}

      {subTab === 'historial' && (
        <SolicitudesHistorialTable historial={historial} />
      )}

      {subTab === 'usuarios' && (
        <ClientesTab
          clientes={clientes}
          cargando={cargandoClientes}
          onRecargar={onRecargarClientes}
          onVerHistorialDiagnosticos={onVerHistorialDiagnosticos}
        />
      )}

      {/* Modales de Aprobación y Rechazo */}
      <SolicitudesModals
        modalAprobado={modalAprobado}
        onCloseAprobado={() => setModalAprobado(null)}
        modalRechazo={modalRechazo}
        onCloseRechazo={() => setModalRechazo(null)}
        motivoRechazo={motivoRechazo}
        onMotivoRechazoChange={setMotivoRechazo}
        rechazando={rechazando}
        errorRechazo={errorRechazo}
        onConfirmRechazo={handleConfirmarRechazo}
      />
    </div>
  );
};
