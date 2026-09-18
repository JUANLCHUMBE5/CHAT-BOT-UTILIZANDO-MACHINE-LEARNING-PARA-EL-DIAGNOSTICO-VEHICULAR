import React from 'react';
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  MessageSquare,
  RefreshCw,
} from 'lucide-react';
import { Badge } from '../../common/Badge';
import { Button } from '../../common/Button';
import { Card } from '../../common/Card';
import type { Diagnostico } from '../../../types';

interface DiagnosticosTablaProps {
  diagnosticosPaginados: Diagnostico[];
  cargando: boolean;
  totalProcesados: number;
  paginaActual: number;
  totalPaginas: number;
  elementosPorPagina: number;
  onCambiarPagina: (pagina: number) => void;
  onElementosPorPaginaChange: (cantidad: number) => void;
  onVerDetalle: (d: Diagnostico) => void;
}

export const DiagnosticosTabla: React.FC<DiagnosticosTablaProps> = ({
  diagnosticosPaginados,
  cargando,
  totalProcesados,
  paginaActual,
  totalPaginas,
  elementosPorPagina,
  onCambiarPagina,
  onElementosPorPaginaChange,
  onVerDetalle,
}) => {
  return (
    <Card style={{ padding: 0, overflow: 'hidden' }}>
      {/* 1. Desktop / Tablet Table View */}
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
              <th style={{ padding: '10px 14px' }}>Solicitante</th>
              <th style={{ padding: '10px 14px' }}>Vehículo</th>
              <th style={{ padding: '10px 14px' }}>Síntoma Reportado</th>
              <th style={{ padding: '10px 14px' }}>Diagnóstico IA</th>
              <th style={{ padding: '10px 14px' }}>Estado</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Acción</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={6} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                    <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)' }} />
                    <span style={{ fontSize: '12.5px' }}>Cargando diagnósticos...</span>
                  </div>
                </td>
              </tr>
            ) : diagnosticosPaginados.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
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
              diagnosticosPaginados.map((d) => {
                const tienePlaca =
                  d.placa_vehiculo &&
                  d.placa_vehiculo.trim() !== '' &&
                  !d.placa_vehiculo.toLowerCase().includes('sin placa');

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
                    {/* Solicitante */}
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div
                          style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: '6px',
                            backgroundColor: '#f1f5f9',
                            color: '#475569',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                            border: '1px solid #e2e8f0',
                          }}
                        >
                          <MessageSquare size={13} />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '12.5px' }}>
                            {d.mecanico_nombre || d.cliente_nombre || 'Usuario'}
                          </span>
                          {d.cliente_telefono && (
                            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                              {d.cliente_telefono}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Vehículo */}
                    <td style={{ padding: '10px 14px' }}>
                      {tienePlaca ? (
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '12.5px' }}>
                            {d.placa_vehiculo}
                          </span>
                          {d.marca_modelo && !d.marca_modelo.toLowerCase().includes('no registrado') && (
                            <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                              {d.marca_modelo}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>—</span>
                      )}
                    </td>

                    {/* Síntoma */}
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

                    {/* Diagnóstico ML */}
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '12.5px' }}>
                          {d.falla_predicha}
                        </span>
                        <span
                          style={{
                            fontSize: '10.5px',
                            fontWeight: 600,
                            color: d.confianza >= 80 ? 'var(--status-success-text)' : 'var(--text-muted)',
                          }}
                        >
                          {d.confianza}% confianza
                        </span>
                      </div>
                    </td>

                    {/* Estado */}
                    <td style={{ padding: '10px 14px' }}>
                      <Badge type={d.estado} />
                    </td>

                    {/* Acción Ver Detalle */}
                    <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onVerDetalle(d)}
                      >
                        Ver Detalle
                      </Button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 2. Mobile Card Feed View (Elegante y fácil de leer) */}
      <div className="diagnosticos-mobile-list" style={{ padding: '8px' }}>
        {cargando ? (
          <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)', margin: '0 auto 6px auto' }} />
            <span style={{ fontSize: '12px' }}>Cargando diagnósticos...</span>
          </div>
        ) : diagnosticosPaginados.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <AlertCircle size={26} style={{ margin: '0 auto 6px auto', opacity: 0.6 }} />
            <p style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
              No se encontraron registros
            </p>
          </div>
        ) : (
          diagnosticosPaginados.map((d) => {
            const tienePlaca =
              d.placa_vehiculo &&
              d.placa_vehiculo.trim() !== '' &&
              !d.placa_vehiculo.toLowerCase().includes('sin placa');

            return (
              <div
                key={d.id}
                onClick={() => onVerDetalle(d)}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  cursor: 'pointer',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
                }}
              >
                {/* Header: Placa / Solicitante + Badge de Estado */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 800, fontSize: '13px', color: tienePlaca ? 'var(--primary)' : 'var(--text-main)' }}>
                      {tienePlaca ? d.placa_vehiculo : (d.mecanico_nombre || d.cliente_nombre || 'Diagnóstico')}
                    </span>
                    {d.confianza && (
                      <span style={{ fontSize: '10px', fontWeight: 700, color: '#059669', backgroundColor: '#ecfdf5', padding: '1px 5px', borderRadius: '4px' }}>
                        {d.confianza}%
                      </span>
                    )}
                  </div>
                  <Badge type={d.estado} />
                </div>

                {/* Subinfo: Solicitante / Teléfono + Fecha */}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>{d.mecanico_nombre || d.cliente_nombre || 'Cliente WhatsApp'} • {d.cliente_telefono || ''}</span>
                  <span>{d.fecha_hora ? d.fecha_hora.slice(0, 10) : ''}</span>
                </div>

                {/* Síntoma */}
                <div
                  style={{
                    backgroundColor: '#f8fafc',
                    padding: '6px 8px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    color: 'var(--text-main)',
                    border: '1px solid #f1f5f9',
                    lineHeight: 1.35,
                  }}
                >
                  "{d.sintoma_original}"
                </div>

                {/* Falla predicha */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#4f46e5' }}>
                    🔧 {d.falla_predicha}
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--primary)' }}>
                    Ver detalle →
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination Bar */}
      {!cargando && totalProcesados > 0 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            borderTop: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-main)',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '13px',
              color: 'var(--text-secondary)',
            }}
          >
            <span>Mostrar</span>
            <select
              value={elementosPorPagina}
              onChange={(e) => onElementosPorPaginaChange(Number(e.target.value))}
              style={{
                padding: '4px 8px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '12px',
                backgroundColor: '#ffffff',
              }}
            >
              <option value={10}>10</option>
            </select>
            <span>por página</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => onCambiarPagina(1)}
              disabled={paginaActual <= 1}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                height: '32px',
                padding: '0 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                fontSize: '12px',
                fontWeight: 600,
                color: paginaActual <= 1 ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual <= 1 ? 'not-allowed' : 'pointer',
                opacity: paginaActual <= 1 ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Primera página"
            >
              <ChevronsLeft size={14} />
              <span>Primera</span>
            </button>

            <button
              type="button"
              onClick={() => onCambiarPagina(paginaActual - 1)}
              aria-label="Página anterior"
              disabled={paginaActual <= 1}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: paginaActual <= 1 ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual <= 1 ? 'not-allowed' : 'pointer',
                opacity: paginaActual <= 1 ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Página anterior"
            >
              <ChevronLeft size={16} />
            </button>

            <span
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                padding: '0 6px',
                whiteSpace: 'nowrap',
              }}
            >
              Página {paginaActual} de {totalPaginas}
            </span>

            <button
              type="button"
              onClick={() => onCambiarPagina(paginaActual + 1)}
              aria-label="Página siguiente"
              disabled={paginaActual >= totalPaginas}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: paginaActual >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual >= totalPaginas ? 'not-allowed' : 'pointer',
                opacity: paginaActual >= totalPaginas ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Página siguiente"
            >
              <ChevronRight size={16} />
            </button>

            <button
              type="button"
              onClick={() => onCambiarPagina(totalPaginas)}
              disabled={paginaActual >= totalPaginas}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                height: '32px',
                padding: '0 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                fontSize: '12px',
                fontWeight: 600,
                color: paginaActual >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual >= totalPaginas ? 'not-allowed' : 'pointer',
                opacity: paginaActual >= totalPaginas ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Última página"
            >
              <span>Última</span>
              <ChevronsRight size={14} />
            </button>
          </div>
        </div>
      )}
    </Card>
  );
};
