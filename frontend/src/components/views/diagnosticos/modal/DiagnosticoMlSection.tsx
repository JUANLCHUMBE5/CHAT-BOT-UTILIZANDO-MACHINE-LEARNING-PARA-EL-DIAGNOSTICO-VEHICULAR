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
    <div
      style={{
        border: '1px solid var(--border-color)',
        borderRadius: '10px',
        padding: '12px 14px',
        backgroundColor: '#ffffff',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '8px',
          flexWrap: 'wrap',
          gap: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={15} style={{ color: '#2563eb' }} />
          <strong style={{ fontSize: '12.5px', color: 'var(--text-main)' }}>
            Confianza ML · Linear SVM (TF-IDF)
          </strong>
        </div>
        <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
          Modelo: <strong>{diagnostico.version_modelo_ml || 'C1_FASE10_FINAL'}</strong>
        </span>
      </div>

      {diagnostico.sintoma_normalizado && (
        <div
          style={{
            marginBottom: '8px',
            padding: '6px 10px',
            backgroundColor: '#f8fafc',
            borderRadius: '6px',
            border: '1px solid #e2e8f0',
            fontSize: '11px',
          }}
        >
          <div style={{ color: '#475569', fontWeight: 700, fontSize: '10.5px', marginBottom: '2px' }}>
            ⚙️ Normalización léxica (Entrada vector TF-IDF):
          </div>
          <div
            style={{
              fontFamily: 'monospace',
              color: '#1e293b',
              fontSize: '10px',
              wordBreak: 'break-word',
              lineHeight: 1.3,
            }}
          >
            {diagnostico.sintoma_normalizado}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
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
                backgroundColor: esPrincipal ? '#f8faff' : '#f8fafc',
                padding: '8px 10px',
                borderRadius: '6px',
                border: esPrincipal ? '1px solid #bfdbfe' : '1px solid var(--border-color)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '4px',
                  fontSize: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
                  <span
                    style={{
                      color: 'var(--text-main)',
                      fontWeight: esPrincipal ? 700 : 500,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {prediccion.orden}. {prediccion.falla}
                  </span>
                  {esPrincipal && (
                    <span
                      style={{
                        fontSize: '9.5px',
                        fontWeight: 700,
                        backgroundColor: '#eff6ff',
                        color: '#1d4ed8',
                        padding: '1px 5px',
                        borderRadius: '4px',
                        border: '1px solid #bfdbfe',
                        flexShrink: 0,
                      }}
                    >
                      Top 1
                    </span>
                  )}
                </div>
                <strong style={{ color: textColor, fontSize: '12px', whiteSpace: 'nowrap' }}>
                  {prediccion.probabilidad}%
                </strong>
              </div>
              <div
                style={{
                  width: '100%',
                  height: '6px',
                  borderRadius: '999px',
                  backgroundColor: '#e2e8f0',
                  overflow: 'hidden',
                }}
              >
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
    </div>
  );
};
