import React from 'react';
import { Cpu } from 'lucide-react';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoMlSectionProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoMlSection: React.FC<DiagnosticoMlSectionProps> = ({
  diagnostico,
}) => {
  return (
    <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: '#eff6ff',
              color: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Cpu size={16} />
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            1. Comparación del Clasificador ML (SVM / TF-IDF)
          </h4>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Modelo: <strong>{diagnostico.version_modelo_ml || '2.2.0-external-audited'}</strong>
        </span>
      </div>

      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 14px 0' }}>
        Distribución de probabilidades por clase calculadas para este síntoma:
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {diagnostico.predicciones_ml.map((prediccion) => {
          const esPrincipal = prediccion.orden === 1;
          const barColor = esPrincipal
            ? 'linear-gradient(90deg, #2563eb 0%, #3b82f6 100%)'
            : prediccion.orden === 2
            ? 'linear-gradient(90deg, #7c3aed 0%, #a855f7 100%)'
            : '#94a3b8';
          const textColor = esPrincipal ? '#2563eb' : prediccion.orden === 2 ? '#7c3aed' : '#64748b';

          return (
            <div
              key={`${prediccion.orden}-${prediccion.falla}`}
              style={{
                backgroundColor: esPrincipal ? '#f8faff' : '#ffffff',
                padding: esPrincipal ? '10px 12px' : '6px 0',
                borderRadius: '8px',
                border: esPrincipal ? '1px solid #dbeafe' : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '6px', fontSize: '13px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: 'var(--text-main)', fontWeight: esPrincipal ? 700 : 500 }}>
                    {prediccion.orden}. {prediccion.falla}
                  </span>
                  {esPrincipal && (
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 700,
                        backgroundColor: '#eff6ff',
                        color: '#1d4ed8',
                        padding: '1px 6px',
                        borderRadius: '6px',
                        border: '1px solid #bfdbfe',
                      }}
                    >
                      Predicción Ganadora
                    </span>
                  )}
                </div>
                <strong style={{ color: textColor, fontSize: '13px', whiteSpace: 'nowrap' }}>
                  {prediccion.probabilidad}%
                </strong>
              </div>
              <div style={{ width: '100%', height: '8px', borderRadius: '999px', backgroundColor: '#e2e8f0', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${Math.max(1, Math.min(100, prediccion.probabilidad))}%`,
                    height: '100%',
                    borderRadius: '999px',
                    background: barColor,
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: '16px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12px', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
        <span>🎯 Hipótesis Seleccionada: <strong>{diagnostico.falla_predicha}</strong></span>
        <span>📊 Confianza: <strong>{diagnostico.confianza}%</strong></span>
      </div>
    </div>
  );
};
