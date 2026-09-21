import React from 'react';
import { Clock, History, AlertTriangle } from 'lucide-react';
import type { SolicitudAcceso } from '../../../types';
import { useSolicitudesActions } from '../../../hooks/useSolicitudesActions';
import {
  SolicitudesPendientesTable,
  SolicitudesHistorialTable,
  SolicitudesModals,
} from './solicitudes';

export interface SolicitudesTabProps {
  solicitudes: SolicitudAcceso[];
  cargando: boolean;
  onRecargar: () => void;
}

export const SolicitudesTab: React.FC<SolicitudesTabProps> = ({
  solicitudes,
  cargando,
  onRecargar,
}) => {
  const {
    subSeccion,
    setSubSeccion,
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
  } = useSolicitudesActions({ onRecargar });

  const pendientes = solicitudes.filter((s) => s.estado === 'pendiente');
  const historial = solicitudes.filter((s) => s.estado !== 'pendiente');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Banner de error */}
      {notificacionError && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#b91c1c',
            fontSize: '13px',
          }}
        >
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
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

      {/* Navegación por sub-secciones */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <button
          type="button"
          onClick={() => setSubSeccion('pendientes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: subSeccion === 'pendientes' ? '#3b82f6' : 'transparent',
            color: subSeccion === 'pendientes' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.2s ease',
          }}
        >
          <Clock size={16} />
          <span>Pendientes por Revisar</span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 700,
              backgroundColor: subSeccion === 'pendientes' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(245, 158, 11, 0.15)',
              color: subSeccion === 'pendientes' ? '#ffffff' : '#d97706',
            }}
          >
            {pendientes.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setSubSeccion('historial')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: subSeccion === 'historial' ? '#3b82f6' : 'transparent',
            color: subSeccion === 'historial' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.2s ease',
          }}
        >
          <History size={16} />
          <span>Historial de Solicitudes</span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 700,
              backgroundColor: subSeccion === 'historial' ? 'rgba(255, 255, 255, 0.25)' : '#f1f5f9',
              color: subSeccion === 'historial' ? '#ffffff' : 'var(--text-muted)',
            }}
          >
            {historial.length}
          </span>
        </button>
      </div>

      {/* Contenido según pestaña */}
      {subSeccion === 'pendientes' ? (
        <SolicitudesPendientesTable
          pendientes={pendientes}
          aprobandoId={aprobandoId}
          cargando={cargando}
          onAprobar={handleAprobarSolicitud}
          onRechazar={handleAbrirModalRechazo}
        />
      ) : (
        <SolicitudesHistorialTable historial={historial} />
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
