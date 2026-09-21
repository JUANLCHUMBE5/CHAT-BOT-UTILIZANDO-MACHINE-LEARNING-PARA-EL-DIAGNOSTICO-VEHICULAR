import React from 'react';
import type { SolicitudAcceso } from '../../../../types';

interface SolicitudesHistorialTableProps {
  historial: SolicitudAcceso[];
}

export const SolicitudesHistorialTable: React.FC<SolicitudesHistorialTableProps> = ({
  historial,
}) => {
  return (
    <div style={{ backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Usuario</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Teléfono / ID</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Estado</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Solicitado</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Revisado por / Fecha</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Motivo / Observaciones</th>
            </tr>
          </thead>
          <tbody>
            {historial.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No hay solicitudes registradas en el historial.
                </td>
              </tr>
            ) : (
              historial.map((s) => (
                <tr key={s.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                    {s.usuario_nombre}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                    {s.telefono}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '2px 8px',
                        borderRadius: '10px',
                        fontSize: '11px',
                        fontWeight: 600,
                        backgroundColor:
                          s.estado === 'aprobada'
                            ? 'rgba(16, 185, 129, 0.15)'
                            : 'rgba(239, 68, 68, 0.15)',
                        color: s.estado === 'aprobada' ? '#047857' : '#b91c1c',
                        textTransform: 'capitalize',
                      }}
                    >
                      {s.estado}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: '12px' }}>
                    {s.solicitado_en}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                    {s.revisado_por ? (
                      <div>
                        <span style={{ fontWeight: 500 }}>{s.revisado_por}</span>
                        <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>{s.revisado_en || '—'}</div>
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '12px', maxWidth: '240px' }}>
                    {s.motivo_rechazo ? (
                      <span style={{ color: '#b91c1c' }}>Rechazo: {s.motivo_rechazo}</span>
                    ) : s.observaciones ? (
                      <span>{s.observaciones}</span>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
