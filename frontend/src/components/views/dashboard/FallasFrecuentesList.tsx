import React from 'react';
import { ChevronRight, AlertTriangle } from 'lucide-react';
import { Card } from '../../common/Card';
import type { ResumenMetricas } from '../../../types';

interface FallasFrecuentesListProps {
  metricas: ResumenMetricas;
  onIrAFallas?: () => void;
}

export const FallasFrecuentesList: React.FC<FallasFrecuentesListProps> = ({
  metricas,
  onIrAFallas,
}) => {
  const fallas = metricas.fallas_frecuentes || [];
  const total = metricas.diagnosticos_realizados ?? metricas.diagnosticos_mes ?? 0;

  // Asegurar orden mayor a menor y limitar a Top 5
  const topFallas = [...fallas]
    .sort((a, b) => b.cantidad - a.cantidad)
    .slice(0, 5);

  const tieneFallas = topFallas.length > 0;

  return (
    <Card className="dashboard-fallas-card" style={{ padding: '16px 18px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '12px',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>
            Fallas más frecuentes del período
          </h3>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
            Top 5 averías diagnosticadas por volumen
          </p>
        </div>

        {onIrAFallas && (
          <button
            type="button"
            onClick={onIrAFallas}
            className="ver-todas-fallas-btn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              background: 'none',
              border: 'none',
              color: 'var(--primary, #f97316)',
              fontSize: '11.5px',
              fontWeight: 700,
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: '6px',
              transition: 'background-color 0.15s',
            }}
          >
            <span>Ver todas las fallas</span>
            <ChevronRight size={14} aria-hidden="true" />
          </button>
        )}
      </div>

      {tieneFallas ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {topFallas.map((item, index) => {
            const porcentaje = total > 0 ? ((item.cantidad / total) * 100).toFixed(1) : '0.0';
            const pctNum = total > 0 ? Math.min(100, Math.round((item.cantidad / total) * 100)) : 0;

            return (
              <div
                key={`${item.falla}-${index}`}
                className="falla-frecuente-row"
                style={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  backgroundColor: 'var(--bg-subtle, #f8fafc)',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  gap: '12px',
                }}
              >
                {/* Barra de progreso tenue de fondo */}
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: `${pctNum}%`,
                    backgroundColor: 'rgba(249, 115, 22, 0.07)',
                    zIndex: 0,
                    pointerEvents: 'none',
                  }}
                  aria-hidden="true"
                />

                {/* Contenido con z-index */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', zIndex: 1, minWidth: 0, flex: 1 }}>
                  <span
                    style={{
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      backgroundColor: 'rgba(249, 115, 22, 0.15)',
                      color: 'var(--primary, #ea580c)',
                      fontSize: '10px',
                      fontWeight: 800,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {index + 1}
                  </span>
                  <span
                    style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      color: 'var(--text-main)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={item.falla}
                  >
                    {item.falla}
                  </span>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    zIndex: 1,
                    flexShrink: 0,
                  }}
                >
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary, #ea580c)' }}>
                    {item.cantidad} {item.cantidad === 1 ? 'caso' : 'casos'}
                  </span>
                  <span
                    style={{
                      fontSize: '10.5px',
                      fontWeight: 600,
                      color: 'var(--text-muted)',
                      backgroundColor: '#ffffff',
                      border: '1px solid var(--border-color, #e2e8f0)',
                      borderRadius: '4px',
                      padding: '1px 5px',
                      minWidth: '40px',
                      textAlign: 'center',
                    }}
                  >
                    {porcentaje}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div
          style={{
            padding: '24px 16px',
            textAlign: 'center',
            backgroundColor: 'var(--bg-subtle, #f8fafc)',
            borderRadius: '8px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <AlertTriangle size={20} style={{ color: '#94a3b8' }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            No hay fallas registradas en este período
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Los diagnósticos realizados aparecerán clasificados aquí automáticamente.
          </span>
        </div>
      )}
    </Card>
  );
};
