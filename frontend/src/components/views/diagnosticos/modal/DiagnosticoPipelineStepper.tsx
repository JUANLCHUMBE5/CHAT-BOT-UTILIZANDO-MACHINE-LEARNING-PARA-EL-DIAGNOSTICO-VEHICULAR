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
    <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={18} style={{ color: 'var(--primary)' }} />
          <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Trazabilidad del Pipeline de Procesamiento
          </h4>
        </div>
        <span
          style={{
            fontSize: '12px',
            color: 'var(--text-muted)',
            backgroundColor: 'var(--bg-subtle)',
            padding: '4px 10px',
            borderRadius: '20px',
            border: '1px solid var(--border-color)',
          }}
        >
          ⏱️ Latencia de Consulta Actual: <strong>{diagnostico.duracion_ms} ms</strong>
          {diagnostico.desde_cache ? ' · ⚡ Servido desde Caché' : ''}
        </span>
      </div>

      {diagnostico.desde_cache && (
        <div
          style={{
            fontSize: '11px',
            color: '#0369a1',
            backgroundColor: '#f0f9ff',
            border: '1px solid #bae6fd',
            borderRadius: '6px',
            padding: '6px 10px',
            marginBottom: '12px',
          }}
        >
          ℹ️ <strong>Consulta resuelta instantáneamente desde Caché.</strong> Las etapas a continuación reflejan la telemetría de la <em>inferencia original registrada</em> ({diagnostico.etapas_procesamiento?.reduce((acc, e) => acc + (e.duracion_ms || 0), 0) || 0} ms), independiente de la latencia actual de consulta ({diagnostico.duracion_ms} ms).
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
        {diagnostico.etapas_procesamiento.map((etapa, index) => {
          const completada = etapa.estado === 'completado';
          const enCola = etapa.estado === 'en_cola';
          const degradado = etapa.estado === 'degradado';
          const badgeColor = completada ? '#059669' : enCola ? '#d97706' : degradado ? '#e11d48' : '#64748b';
          const badgeBg = completada ? '#ecfdf5' : enCola ? '#fffbeb' : degradado ? '#fff1f2' : '#f8fafc';

          const nombreEtapa = (degradado && etapa.clave === 'llm' && !etapa.nombre.includes('Fallback'))
            ? 'Síntesis Gemini (Fallback ML+RAG)'
            : etapa.nombre;

          const detalleEtapa = (degradado && etapa.clave === 'llm')
            ? (etapa.detalle?.toLowerCase().includes('fallback')
                ? etapa.detalle
                : 'Fallback determinista activo: síntesis externa omitida o límite de cuota superado.')
            : etapa.detalle;

          return (
            <div
              key={`${etapa.clave}-${index}`}
              style={{
                padding: '12px 14px',
                borderRadius: '10px',
                backgroundColor: badgeBg,
                border: `1px solid ${badgeColor}30`,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span
                    style={{
                      width: '22px',
                      height: '22px',
                      borderRadius: '50%',
                      backgroundColor: badgeColor,
                      color: '#ffffff',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '11px',
                      fontWeight: 700,
                    }}
                  >
                    {index + 1}
                  </span>
                  <span style={{ fontSize: '10px', fontWeight: 700, color: badgeColor, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {etapa.estado.replace('_', ' ')}
                  </span>
                </div>
                <strong style={{ fontSize: '12px', color: 'var(--text-main)', display: 'block', lineHeight: 1.3 }}>
                  {nombreEtapa}
                </strong>
              </div>

              <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: `1px dashed ${badgeColor}25` }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {etapa.duracion_ms} ms
                </span>
                {detalleEtapa && (
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px', lineHeight: 1.3 }}>
                    {detalleEtapa}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
