import React from 'react';
import { History } from 'lucide-react';
import type { SolicitudAcceso } from '../../../../types';

interface SolicitudesHistorialTableProps {
  historial: SolicitudAcceso[];
}

export const SolicitudesHistorialTable: React.FC<SolicitudesHistorialTableProps> = ({
  historial,
}) => {
  if (historial.length === 0) {
    return (
      <div
        style={{
          padding: '32px',
          textAlign: 'center',
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
          fontSize: '13px',
        }}
      >
        <History size={32} style={{ margin: '0 auto 8px auto', opacity: 0.5 }} />
        <div>No hay solicitudes registradas en el historial.</div>
      </div>
    );
  }

  return (
    <div>
      {/* Vista Desktop: Tabla */}
      <div
        className="responsive-table-desktop"
        style={{
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12.5px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Usuario</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Teléfono / ID</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Resultado</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Solicitado</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Revisado por / Fecha</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Observaciones</th>
            </tr>
          </thead>
          <tbody>
            {historial.map((s) => (
              <tr key={s.id} className="table-row-hover" style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-main)' }}>
                  {s.usuario_nombre}
                </td>
                <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>
                  {s.telefono}
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      fontSize: '11px',
                      fontWeight: 700,
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
                <td style={{ padding: '10px 14px', color: 'var(--text-muted)', fontSize: '12px' }}>
                  {s.solicitado_en}
                </td>
                <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                  {s.revisado_por ? (
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{s.revisado_por}</span>
                      <div style={{ color: 'var(--text-muted)', fontSize: '10.5px' }}>{s.revisado_en || '—'}</div>
                    </div>
                  ) : (
                    '—'
                  )}
                </td>
                <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', fontSize: '12px', maxWidth: '240px' }}>
                  {s.motivo_rechazo ? (
                    <span style={{ color: '#b91c1c', fontWeight: 500 }}>Rechazo: {s.motivo_rechazo}</span>
                  ) : s.observaciones ? (
                    <span>{s.observaciones}</span>
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Vista Móvil: Cards Feed */}
      <div className="responsive-cards-mobile">
        {historial.map((s) => (
          <div
            key={s.id}
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              padding: '10px 12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-main)' }}>
                {s.usuario_nombre}
              </span>
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: '10px',
                  fontSize: '10.5px',
                  fontWeight: 700,
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
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)' }}>
              <span>📱 {s.telefono}</span>
              <span style={{ color: 'var(--text-muted)' }}>{s.solicitado_en}</span>
            </div>

            {s.revisado_por && (
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', backgroundColor: '#f8fafc', padding: '4px 8px', borderRadius: '4px' }}>
                Revisado por: <strong style={{ color: 'var(--text-main)' }}>{s.revisado_por}</strong> {s.revisado_en ? `· ${s.revisado_en}` : ''}
              </div>
            )}

            {(s.motivo_rechazo || s.observaciones) && (
              <div style={{ fontSize: '11px', color: s.motivo_rechazo ? '#b91c1c' : 'var(--text-secondary)', fontStyle: 'italic' }}>
                {s.motivo_rechazo ? `Motivo: ${s.motivo_rechazo}` : `Observaciones: ${s.observaciones}`}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
