import React from 'react';
import { BookOpen, Clock, Sparkles } from 'lucide-react';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoRagSectionProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoRagSection: React.FC<DiagnosticoRagSectionProps> = ({
  diagnostico,
}) => {
  return (
    <>
      {/* Section 2: Evidencia Recuperada por RAG */}
      <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                backgroundColor: '#f0fdf4',
                color: '#16a34a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <BookOpen size={16} />
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              2. Evidencia Recuperada por RAG (Manuales Técnicos)
            </h4>
          </div>
          {diagnostico.similitud_rag !== undefined && (
            <span
              style={{
                fontSize: '12px',
                fontWeight: 600,
                padding: '3px 10px',
                borderRadius: '12px',
                backgroundColor: diagnostico.similitud_rag > 0 ? '#ecfdf5' : '#f1f5f9',
                color: diagnostico.similitud_rag > 0 ? '#059669' : '#64748b',
                border: `1px solid ${diagnostico.similitud_rag > 0 ? '#a7f3d0' : '#e2e8f0'}`,
              }}
            >
              Similitud RAG: <strong>{diagnostico.similitud_rag}%</strong>
            </span>
          )}
        </div>

        {diagnostico.fuente_manual && (
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', fontStyle: 'italic' }}>
            Referencia documental: {diagnostico.fuente_manual}
          </div>
        )}

        <pre
          style={{
            fontSize: '13px',
            fontFamily: 'inherit',
            whiteSpace: 'pre-wrap',
            backgroundColor: 'var(--bg-subtle)',
            padding: '14px',
            borderRadius: '8px',
            color: 'var(--text-main)',
            lineHeight: 1.5,
            margin: 0,
            border: '1px solid var(--border-color)',
          }}
        >
          {diagnostico.procedimiento_rag}
        </pre>
      </div>

      {/* Section 3: Tiempo Estimado y Gravedad */}
      <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: '#fffbeb',
              color: '#d97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Clock size={16} />
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            3. Tiempo Estimado y Gravedad
          </h4>
        </div>
        <div
          style={{
            fontSize: '13px',
            color: 'var(--text-secondary)',
            backgroundColor: 'var(--bg-subtle)',
            padding: '12px 14px',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            lineHeight: 1.5,
          }}
        >
          {diagnostico.tiempo_gravedad}
        </div>
      </div>

      {/* Section 4: Síntesis Técnica Gemini (si existe) */}
      {diagnostico.sintesis_llm && (
        <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '6px',
                  backgroundColor: '#faf5ff',
                  color: '#9333ea',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Sparkles size={16} />
              </div>
              <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                4. Síntesis Técnica de Gemini
              </h4>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Modelo: <strong>{diagnostico.llm_modelo || 'Gemini-1.5-Flash'}</strong>
            </span>
          </div>

          <div
            style={{
              fontSize: '13px',
              whiteSpace: 'pre-wrap',
              color: 'var(--text-secondary)',
              lineHeight: 1.55,
              backgroundColor: 'var(--bg-subtle)',
              padding: '14px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
            }}
          >
            {diagnostico.sintesis_llm}
          </div>

          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-color)', fontSize: '11px', color: 'var(--text-muted)' }}>
            <span>📥 Tokens Entrada: <strong>{diagnostico.tokens_entrada}</strong></span>
            <span>📤 Tokens Salida: <strong>{diagnostico.tokens_salida}</strong></span>
          </div>
        </div>
      )}
    </>
  );
};
