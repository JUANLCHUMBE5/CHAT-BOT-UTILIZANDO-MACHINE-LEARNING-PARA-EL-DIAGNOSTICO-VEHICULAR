import React from 'react';
import { Cpu } from 'lucide-react';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoPipelineStepperProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoPipelineStepper: React.FC<DiagnosticoPipelineStepperProps> = ({
  diagnostico,
}) => {
  return (
    <div
      style={{
        border: '1px solid var(--border-color)',
        borderRadius: '10px',
        padding: '10px 12px',
        backgroundColor: '#ffffff',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={15} style={{ color: '#2563eb' }} />
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-main)' }}>
            Pipeline de Procesamiento en Cascada
          </span>
        </div>
        <span
          style={{
            fontSize: '10.5px',
            color: '#1e40af',
            backgroundColor: '#eff6ff',
            padding: '2px 8px',
            borderRadius: '12px',
            fontWeight: 600,
            border: '1px solid #bfdbfe',
          }}
        >
          ⏱️ {diagnostico.duracion_ms} ms {diagnostico.desde_cache ? '· Caché' : ''}
        </span>
      </div>

      {diagnostico.desde_cache && (
        <div
          style={{
            fontSize: '10.5px',
            color: '#0369a1',
            backgroundColor: '#f0f9ff',
            border: '1px solid #bae6fd',
            borderRadius: '6px',
            padding: '4px 8px',
            marginBottom: '8px',
          }}
        >
          ⚡ Servido desde memoria caché.
        </div>
      )}

      {/* Grid de 4 etapas en 1 sola fila horizontal */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '6px',
        }}
      >
        {diagnostico.etapas_procesamiento.map((etapa, index) => {
          const completada = etapa.estado === 'completado';
          const enCola = etapa.estado === 'en_cola';
          const degradado = etapa.estado === 'degradado';
          const badgeColor = completada ? '#059669' : enCola ? '#d97706' : degradado ? '#e11d48' : '#64748b';
          const badgeBg = completada ? '#ecfdf5' : enCola ? '#fffbeb' : degradado ? '#fff1f2' : '#f8fafc';

          const nombreCorto =
            etapa.clave === 'normalizacion'
              ? 'Normalización'
              : etapa.clave === 'ml'
              ? 'Linear SVM'
              : etapa.clave === 'rag'
              ? 'RAG Manuales'
              : etapa.clave === 'llm'
              ? (degradado ? 'Fallback ML+RAG' : 'Síntesis Gemini')
              : etapa.nombre;

          return (
            <div
              key={`${etapa.clave}-${index}`}
              style={{
                padding: '6px 8px',
                borderRadius: '8px',
                backgroundColor: badgeBg,
                border: `1px solid ${badgeColor}30`,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minHeight: '64px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span
                  style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    backgroundColor: badgeColor,
                    color: '#ffffff',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '10px',
                    fontWeight: 700,
                  }}
                >
                  {index + 1}
                </span>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 700,
                    color: badgeColor,
                    textTransform: 'uppercase',
                  }}
                >
                  {etapa.duracion_ms} ms
                </span>
              </div>

              <div>
                <strong
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-main)',
                    display: 'block',
                    lineHeight: 1.2,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={etapa.nombre}
                >
                  {nombreCorto}
                </strong>
                <span
                  style={{
                    fontSize: '9.5px',
                    color: badgeColor,
                    fontWeight: 600,
                    textTransform: 'capitalize',
                  }}
                >
                  {etapa.estado.replace('_', ' ')}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
