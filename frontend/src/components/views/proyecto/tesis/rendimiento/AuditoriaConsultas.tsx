import React, { useState } from 'react';
import { Search, Eye, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
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

const ITEMS_POR_PAGINA = 10;

export const AuditoriaConsultas: React.FC<AuditoriaConsultasProps> = ({
  diagnosticos,
  cargando,
  busqueda,
  onBusquedaChange,
  onVerDetalle,
}) => {
  const [pagina, setPagina] = useState(1);

  // Filtrar consultas para ignorar saludos vacíos si no hay búsqueda
  const totalItems = diagnosticos.length;
  const totalPaginas = Math.max(1, Math.ceil(totalItems / ITEMS_POR_PAGINA));
  const paginaAjustada = Math.min(pagina, totalPaginas);

  const inicio = (paginaAjustada - 1) * ITEMS_POR_PAGINA;
  const itemsPagina = diagnosticos.slice(inicio, inicio + ITEMS_POR_PAGINA);

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
            Auditoría de Consultas WhatsApp (Inferencia y Trazabilidad)
          </h4>
          <span style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
            Consultas recibidas con predicción de Linear SVM y opción de vincular a caso Post-test
          </span>
        </div>

        <div style={{ width: '280px' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Buscar por síntoma, falla o placa..."
              value={busqueda}
              onChange={(e) => {
                onBusquedaChange(e.target.value);
                setPagina(1);
              }}
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
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
              <th style={{ padding: '10px 14px', width: '110px' }}>Fecha / Hora</th>
              <th style={{ padding: '10px 14px', width: '160px' }}>Remitente</th>
              <th style={{ padding: '10px 14px' }}>Síntoma Reportado</th>
              <th style={{ padding: '10px 14px' }}>Predicción Linear SVM</th>
              <th style={{ padding: '10px 14px', width: '110px' }}>Estado</th>
              <th style={{ padding: '10px 14px', width: '70px', textAlign: 'right' }}>Acción</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                    <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)' }} />
                    <span>Cargando consultas de CarBot...</span>
                  </div>
                </td>
              </tr>
            ) : itemsPagina.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No se encontraron consultas registradas en este período.
                </td>
              </tr>
            ) : (
              itemsPagina.map((d) => (
                <tr
                  key={d.id}
                  className="table-row-hover"
                  style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: '#ffffff' }}
                >
                  <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: 'var(--text-secondary)', fontSize: '11px' }}>
                    {d.fecha_hora ? new Date(d.fecha_hora).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' }) : 'Reciente'}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '11.5px' }}>
                      {d.mecanico_nombre || d.cliente_nombre || 'Mecánico WhatsApp'}
                    </div>
                    <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                      {d.cliente_telefono ? `WhatsApp (${d.cliente_telefono})` : 'Canal WhatsApp'}
                    </div>
                  </td>
                  <td style={{ padding: '10px 14px', maxWidth: '280px' }}>
                    <div
                      style={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        color: 'var(--text-main)',
                      }}
                      title={d.sintoma_original || d.sintoma_normalizado}
                    >
                      "{d.sintoma_original || d.sintoma_normalizado}"
                    </div>
                  </td>
                  <td style={{ padding: '10px 14px', maxWidth: '260px' }}>
                    <div
                      style={{
                        fontWeight: 600,
                        color: '#047857',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                      title={d.falla_predicha}
                    >
                      {d.falla_predicha}
                    </div>
                    {typeof d.confianza === 'number' && (
                      <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                        {d.confianza.toFixed(1)}% certidumbre SVM
                      </div>
                    )}
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
                        fontSize: '11px',
                        fontWeight: 600,
                        borderRadius: '5px',
                        border: '1px solid var(--border-color)',
                        backgroundColor: '#ffffff',
                        color: 'var(--primary)',
                        cursor: 'pointer',
                      }}
                      title="Ver trazabilidad o vincular a caso Post-test"
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

      {/* Paginación Compacta */}
      {totalItems > ITEMS_POR_PAGINA && (
        <div
          style={{
            padding: '10px 16px',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            backgroundColor: '#ffffff',
          }}
        >
          <span>
            Mostrando {inicio + 1}–{Math.min(inicio + ITEMS_POR_PAGINA, totalItems)} de {totalItems} consultas
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              type="button"
              disabled={paginaAjustada <= 1}
              onClick={() => setPagina((p) => Math.max(1, p - 1))}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '5px',
                border: '1px solid var(--border-color)',
                backgroundColor: paginaAjustada <= 1 ? '#f1f5f9' : '#ffffff',
                color: paginaAjustada <= 1 ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaAjustada <= 1 ? 'not-allowed' : 'pointer',
              }}
            >
              <ChevronLeft size={12} /> Anterior
            </button>
            <span style={{ padding: '4px 8px', fontWeight: 700 }}>
              {paginaAjustada} / {totalPaginas}
            </span>
            <button
              type="button"
              disabled={paginaAjustada >= totalPaginas}
              onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '5px',
                border: '1px solid var(--border-color)',
                backgroundColor: paginaAjustada >= totalPaginas ? '#f1f5f9' : '#ffffff',
                color: paginaAjustada >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaAjustada >= totalPaginas ? 'not-allowed' : 'pointer',
              }}
            >
              Siguiente <ChevronRight size={12} />
            </button>
          </div>
        </div>
      )}
    </Card>
  );
};
