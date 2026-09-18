import React from 'react';
import { Search, Eye, RefreshCw } from 'lucide-react';
import { Card } from '../../../../common/Card';
import { Badge } from '../../../../common/Badge';
import type { Diagnostico } from '../../../../../types';

interface AuditoriaConsultasProps {
  diagnosticos: Diagnostico[];
  cargando: boolean;
  busqueda: string;
  onBusquedaChange: (valor: string) => void;
  onVerDetalle: (diag: Diagnostico) => void;
}

export const AuditoriaConsultas: React.FC<AuditoriaConsultasProps> = ({
  diagnosticos,
  cargando,
  busqueda,
  onBusquedaChange,
  onVerDetalle,
}) => {
  return (
    <Card style={{ padding: 0, overflow: 'hidden', border: '1px solid var(--border-color)' }}>
      {/* Barra de Búsqueda y Título de Auditoría */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: 'var(--bg-subtle)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: 'var(--text-main)' }}>
            Trazabilidad Individual de Consultas
          </h4>
          <span style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
            Historial de interacciones recibidas vía WhatsApp con predicción de Linear SVM y confirmación física
          </span>
        </div>

        <div style={{ width: '260px' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Filtrar por síntoma o mecánico..."
              value={busqueda}
              onChange={(e) => onBusquedaChange(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 10px 6px 30px',
                fontSize: '12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                outline: 'none',
                backgroundColor: '#ffffff',
              }}
            />
          </div>
        </div>
      </div>

      {/* Tabla de Consultas */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12.5px' }}>
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
              <th style={{ padding: '10px 14px' }}>Fecha / Hora</th>
              <th style={{ padding: '10px 14px' }}>Mecánico / Canal</th>
              <th style={{ padding: '10px 14px' }}>Síntoma Reportado</th>
              <th style={{ padding: '10px 14px' }}>Hipótesis Linear SVM</th>
              <th style={{ padding: '10px 14px' }}>Pipeline</th>
              <th style={{ padding: '10px 14px' }}>Validación Física</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Detalle</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                    <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)' }} />
                    <span>Cargando consultas de CarBot...</span>
                  </div>
                </td>
              </tr>
            ) : diagnosticos.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No se encontraron consultas registradas en este período.
                </td>
              </tr>
            ) : (
              diagnosticos.map((d) => (
                <tr
                  key={d.id}
                  className="table-row-hover"
                  style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: '#ffffff' }}
                >
                  <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: 'var(--text-secondary)', fontSize: '11.5px' }}>
                    {d.fecha_hora ? new Date(d.fecha_hora).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' }) : 'Reciente'}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{d.mecanico_nombre || d.cliente_nombre || 'Mecánico WhatsApp'}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>WhatsApp ({d.cliente_telefono || 'Taller'})</div>
                  </td>
                  <td style={{ padding: '10px 14px', maxWidth: '240px' }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={d.sintoma_original}>
                      "{d.sintoma_original || d.sintoma_normalizado}"
                    </div>
                  </td>
                  <td style={{ padding: '10px 14px', maxWidth: '260px' }}>
                    <div style={{ fontWeight: 600, color: '#047857', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={d.falla_predicha}>
                      {d.falla_predicha}
                    </div>
                    {typeof d.confianza === 'number' && (
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {d.confianza.toFixed(1)}% confianza
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <Badge type={d.modo_diagnostico || 'completo_ml_rag_llm'} size="sm" />
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <Badge type={d.estado} size="sm" />
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                    <button
                      type="button"
                      onClick={() => onVerDetalle(d)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '4px 8px',
                        fontSize: '11.5px',
                        fontWeight: 600,
                        borderRadius: '6px',
                        border: '1px solid var(--border-color)',
                        backgroundColor: '#ffffff',
                        color: 'var(--primary)',
                        cursor: 'pointer',
                      }}
                      title="Ver trazabilidad completa"
                    >
                      <Eye size={12} />
                      <span>Ver</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
