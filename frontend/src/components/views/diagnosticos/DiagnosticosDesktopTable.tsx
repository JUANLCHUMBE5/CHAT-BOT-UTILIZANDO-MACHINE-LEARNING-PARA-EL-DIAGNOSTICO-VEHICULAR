import React from 'react';
import { AlertCircle, RefreshCw, MessageSquare } from 'lucide-react';
import { Badge } from '../../common/Badge';
import { Button } from '../../common/Button';
import type { Diagnostico } from '../../../types';

interface DiagnosticosDesktopTableProps {
  diagnosticos: Diagnostico[];
  cargando: boolean;
  onVerDetalle: (d: Diagnostico) => void;
}

export const DiagnosticosDesktopTable: React.FC<DiagnosticosDesktopTableProps> = ({
  diagnosticos,
  cargando,
  onVerDetalle,
}) => {
  return (
    <div className="diagnosticos-desktop-table" style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr
            style={{
              backgroundColor: 'var(--bg-subtle)',
              borderBottom: '1px solid var(--border-color)',
              fontSize: '11px',
              fontWeight: 700,
              color: 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            <th style={{ padding: '10px 14px' }}>Vehículo</th>
            <th style={{ padding: '10px 14px' }}>Síntoma Reportado</th>
            <th style={{ padding: '10px 14px' }}>Diagnóstico IA</th>
            <th style={{ padding: '10px 14px' }}>Confianza</th>
            <th style={{ padding: '10px 14px' }}>Estado</th>
            <th style={{ padding: '10px 14px' }}>Fecha</th>
            <th style={{ padding: '10px 14px', textAlign: 'right' }}>Acción</th>
          </tr>
        </thead>
        <tbody>
          {cargando ? (
            <tr>
              <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                  <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)' }} />
                  <span style={{ fontSize: '12.5px' }}>Cargando diagnósticos...</span>
                </div>
              </td>
            </tr>
          ) : diagnosticos.length === 0 ? (
            <tr>
              <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                  <AlertCircle size={28} style={{ color: 'var(--text-muted)', opacity: 0.6 }} />
                  <p style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                    No se encontraron registros
                  </p>
                  <p style={{ margin: 0, fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                    Prueba con otros filtros o términos de búsqueda.
                  </p>
                </div>
              </td>
            </tr>
          ) : (
            diagnosticos.map((d) => {
              const tienePlaca =
                d.placa_vehiculo &&
                d.placa_vehiculo.trim() !== '' &&
                !d.placa_vehiculo.toLowerCase().includes('sin placa');

              const tieneMarca = Boolean(
                d.marca_modelo &&
                d.marca_modelo.trim() !== '' &&
                !d.marca_modelo.toLowerCase().includes('no registrado')
              );

              return (
                <tr
                  key={d.id}
                  className="table-row-hover"
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    fontSize: '12.5px',
                    backgroundColor: '#ffffff',
                  }}
                >
                  {/* 1. Prioridad: Vehículo (con solicitante de menor jerarquía) */}
                  <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      {tienePlaca ? (
                        <>
                          <span style={{ fontWeight: 800, color: 'var(--primary)', fontSize: '13px' }}>
                            {d.placa_vehiculo}
                          </span>
                          <span style={{ fontSize: '11px', color: 'var(--text-main)' }}>
                            {tieneMarca ? d.marca_modelo : 'Vehículo registrado'}
                          </span>
                        </>
                      ) : tieneMarca ? (
                        <>
                          <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '12.5px' }}>
                            {d.marca_modelo}
                          </span>
                          <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                            Sin placa
                          </span>
                        </>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '12px', fontStyle: 'italic' }}>
                          Consulta general
                        </span>
                      )}

                      {/* Solicitante con menor jerarquía */}
                      <span style={{ fontSize: '10.5px', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '3px', marginTop: '2px' }}>
                        <MessageSquare size={10} />
                        {d.mecanico_nombre || d.cliente_nombre || 'Usuario'}
                      </span>
                    </div>
                  </td>

                  {/* 2. Síntoma Reportado (Truncado) */}
                  <td style={{ padding: '10px 14px', maxWidth: '240px', color: 'var(--text-main)' }}>
                    <p
                      style={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        margin: 0,
                        fontSize: '12px',
                      }}
                      title={d.sintoma_original}
                    >
                      "{d.sintoma_original}"
                    </p>
                  </td>

                  {/* 3. Diagnóstico IA */}
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ fontWeight: 700, color: '#0f172a', fontSize: '12.5px' }}>
                      {d.falla_predicha}
                    </span>
                  </td>

                  {/* 4. Confianza */}
                  <td style={{ padding: '10px 14px' }}>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 800,
                        padding: '2px 7px',
                        borderRadius: '6px',
                        backgroundColor: d.confianza >= 70 ? '#ecfdf5' : '#fef3c7',
                        color: d.confianza >= 70 ? '#059669' : '#b45309',
                        border: `1px solid ${d.confianza >= 70 ? '#a7f3d0' : '#fde68a'}`,
                        display: 'inline-block',
                      }}
                    >
                      {d.confianza}%
                    </span>
                  </td>

                  {/* 5. Estado */}
                  <td style={{ padding: '10px 14px' }}>
                    <Badge type={d.estado} />
                  </td>

                  {/* 6. Fecha */}
                  <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', fontSize: '11.5px', whiteSpace: 'nowrap' }}>
                    {d.fecha_hora || '—'}
                  </td>

                  {/* 7. Acción: Ver diagnóstico */}
                  <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onVerDetalle(d)}
                      style={{ fontSize: '11.5px', padding: '4px 10px', fontWeight: 700 }}
                    >
                      Ver diagnóstico
                    </Button>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};
