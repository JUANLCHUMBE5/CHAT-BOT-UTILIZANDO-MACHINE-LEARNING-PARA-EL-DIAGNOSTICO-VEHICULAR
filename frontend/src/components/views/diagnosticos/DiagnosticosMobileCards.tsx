import React from 'react';
import { AlertCircle, RefreshCw, ArrowRight } from 'lucide-react';
import { Badge } from '../../common/Badge';
import type { Diagnostico } from '../../../types';

interface DiagnosticosMobileCardsProps {
  diagnosticos: Diagnostico[];
  cargando: boolean;
  onVerDetalle: (d: Diagnostico) => void;
}

export const DiagnosticosMobileCards: React.FC<DiagnosticosMobileCardsProps> = ({
  diagnosticos,
  cargando,
  onVerDetalle,
}) => {
  if (cargando) {
    return (
      <div className="diagnosticos-mobile-list" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)', margin: '0 auto 6px auto' }} />
        <span style={{ fontSize: '12px' }}>Cargando diagnósticos...</span>
      </div>
    );
  }

  if (diagnosticos.length === 0) {
    return (
      <div className="diagnosticos-mobile-list" style={{ padding: '24px', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
        <AlertCircle size={26} style={{ margin: '0 auto 6px auto', opacity: 0.6 }} />
        <p style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
          No se encontraron diagnósticos
        </p>
        <p style={{ margin: '4px 0 0', fontSize: '11.5px', color: 'var(--text-secondary)' }}>
          Prueba con otros filtros o términos de búsqueda.
        </p>
      </div>
    );
  }

  return (
    <div className="diagnosticos-mobile-list" style={{ padding: '2px 0', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {diagnosticos.map((d) => {
        const tienePlaca =
          d.placa_vehiculo &&
          d.placa_vehiculo.trim() !== '' &&
          !d.placa_vehiculo.toLowerCase().includes('sin placa');

        const tieneMarca = Boolean(
          d.marca_modelo &&
          d.marca_modelo.trim() !== '' &&
          !d.marca_modelo.toLowerCase().includes('no registrado')
        );

        const nombreVehiculo = tienePlaca
          ? `${tieneMarca ? d.marca_modelo + ' · ' : ''}${d.placa_vehiculo}`
          : tieneMarca
          ? d.marca_modelo
          : 'Consulta general';

        return (
          <div
            key={d.id}
            onClick={() => onVerDetalle(d)}
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '10px',
              border: '1px solid var(--border-color)',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
              transition: 'all 0.15s ease',
            }}
          >
            {/* 1. Vehículo & 2. Fecha */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
              <div>
                <span
                  style={{
                    fontWeight: 800,
                    fontSize: '13px',
                    color: tienePlaca ? 'var(--primary)' : 'var(--text-main)',
                    display: 'block',
                  }}
                >
                  {nombreVehiculo}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {d.fecha_hora || 'Fecha no registrada'}
                </span>
              </div>
              {/* 6. Estado */}
              <Badge type={d.estado} />
            </div>

            {/* 3. Síntoma Reportado */}
            <div
              style={{
                backgroundColor: '#f8fafc',
                padding: '8px 10px',
                borderRadius: '6px',
                fontSize: '12px',
                color: 'var(--text-main)',
                border: '1px solid #f1f5f9',
                lineHeight: 1.4,
              }}
            >
              "{d.sintoma_original}"
            </div>

            {/* 4. Predicción CarBot & 5. Confianza */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Diagnóstico IA:
                </div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>
                  {d.falla_predicha}
                </div>
              </div>

              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  color: d.confianza >= 70 ? '#059669' : '#b45309',
                  backgroundColor: d.confianza >= 70 ? '#ecfdf5' : '#fef3c7',
                  border: `1px solid ${d.confianza >= 70 ? '#a7f3d0' : '#fde68a'}`,
                  padding: '2px 8px',
                  borderRadius: '6px',
                }}
              >
                {d.confianza}% confianza
              </span>
            </div>

            {/* 7. Acción: Ver diagnóstico → */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingTop: '6px',
                borderTop: '1px solid #f1f5f9',
                fontSize: '11.5px',
                color: 'var(--text-muted)',
              }}
            >
              <span>{d.mecanico_nombre || d.cliente_nombre || 'Mecánico'}</span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontWeight: 700,
                  color: 'var(--primary)',
                }}
              >
                <span>Ver diagnóstico</span>
                <ArrowRight size={13} />
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
