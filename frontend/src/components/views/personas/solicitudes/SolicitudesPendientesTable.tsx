import React from 'react';
import { ShieldCheck, UserCheck, UserX } from 'lucide-react';
import type { SolicitudAcceso } from '../../../../types';

interface SolicitudesPendientesTableProps {
  pendientes: SolicitudAcceso[];
  aprobandoId: string | null;
  cargando: boolean;
  onAprobar: (sol: SolicitudAcceso) => void;
  onRechazar: (sol: SolicitudAcceso) => void;
}

export const SolicitudesPendientesTable: React.FC<SolicitudesPendientesTableProps> = ({
  pendientes,
  aprobandoId,
  cargando,
  onAprobar,
  onRechazar,
}) => {
  if (pendientes.length === 0) {
    return (
      <div
        style={{
          padding: '48px 24px',
          textAlign: 'center',
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
        }}
      >
        <ShieldCheck size={48} style={{ color: '#10b981', marginBottom: '12px', opacity: 0.8 }} />
        <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', margin: '0 0 6px 0' }}>
          No hay solicitudes pendientes
        </h3>
        <p style={{ fontSize: '13px', margin: 0, color: 'var(--text-secondary)' }}>
          Todas las solicitudes de acceso al taller han sido procesadas.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
      {pendientes.map((sol) => (
        <div
          key={sol.id}
          style={{
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                  {sol.usuario_nombre}
                </h4>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  {sol.telefono}
                </span>
              </div>
              <span
                style={{
                  padding: '4px 10px',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: 600,
                  backgroundColor: 'rgba(245, 158, 11, 0.12)',
                  color: '#b45309',
                  textTransform: 'capitalize',
                }}
              >
                Rol: {sol.rol_solicitado || 'Mecánico'}
              </span>
            </div>

            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div>
                <strong style={{ color: 'var(--text-main)' }}>Fecha: </strong>
                {sol.solicitado_en}
              </div>
              {sol.observaciones && (
                <div style={{ fontStyle: 'italic', backgroundColor: 'var(--bg-main)', padding: '8px 10px', borderRadius: '6px' }}>
                  "{sol.observaciones}"
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
            <button
              type="button"
              onClick={() => onAprobar(sol)}
              disabled={aprobandoId === sol.id || cargando}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '9px 14px',
                backgroundColor: '#10b981',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: aprobandoId === sol.id ? 'not-allowed' : 'pointer',
              }}
            >
              <UserCheck size={16} />
              <span>{aprobandoId === sol.id ? 'Aprobando...' : 'Aprobar Mecánico'}</span>
            </button>
            <button
              type="button"
              onClick={() => onRechazar(sol)}
              disabled={aprobandoId === sol.id || cargando}
              style={{
                padding: '9px 14px',
                backgroundColor: '#ffffff',
                color: '#ef4444',
                border: '1px solid #fca5a5',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <UserX size={16} />
              <span>Rechazar</span>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
