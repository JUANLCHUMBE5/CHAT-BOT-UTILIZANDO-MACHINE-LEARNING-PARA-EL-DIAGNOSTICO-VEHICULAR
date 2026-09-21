import React from 'react';
import { BookOpen, Sparkles } from 'lucide-react';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoRagSectionProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoRagSection: React.FC<DiagnosticoRagSectionProps> = ({
  diagnostico,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* 1. Evidencia y Similitud RAG */}
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
            marginBottom: '6px',
            flexWrap: 'wrap',
            gap: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <BookOpen size={15} style={{ color: '#16a34a' }} />
            <strong style={{ fontSize: '12.5px', color: 'var(--text-main)' }}>
              Evidencia RAG · Manuales de Taller OEM
            </strong>
          </div>
          {diagnostico.similitud_rag !== undefined && (
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '12px',
                backgroundColor: diagnostico.similitud_rag > 0 ? '#ecfdf5' : '#f1f5f9',
                color: diagnostico.similitud_rag > 0 ? '#059669' : '#64748b',
                border: `1px solid ${diagnostico.similitud_rag > 0 ? '#a7f3d0' : '#e2e8f0'}`,
              }}
            >
              Similitud: <strong>{diagnostico.similitud_rag}%</strong>
            </span>
          )}
        </div>

        {diagnostico.fuente_manual && (
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px', fontStyle: 'italic' }}>
            Referencia: {diagnostico.fuente_manual}
          </div>
        )}

        <div
          style={{
            fontSize: '11.5px',
            whiteSpace: 'pre-wrap',
            backgroundColor: 'var(--bg-subtle)',
            padding: '10px 12px',
            borderRadius: '6px',
            color: 'var(--text-main)',
            lineHeight: 1.45,
            maxHeight: '170px',
            overflowY: 'auto',
            border: '1px solid var(--border-color)',
            fontFamily: 'inherit',
          }}
        >
          {(diagnostico.procedimiento_rag || 'Sin procedimiento complementario recuperado.')
            .replace(/tolerancias\s+y\s+especificaciones\s+metrológicas\s+oem:?/gi, 'Valores técnicos del procedimiento:')
            .replace(/especificaciones\s+metrológicas\s+oem:?/gi, 'valores técnicos:')}
        </div>
      </div>

      {/* 2. Síntesis Gemini o Fallback Determinista */}
      {diagnostico.sintesis_llm && (
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
              marginBottom: '6px',
              flexWrap: 'wrap',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={15} style={{ color: '#9333ea' }} />
              <strong style={{ fontSize: '12.5px', color: 'var(--text-main)' }}>
                Síntesis Técnica Generativa (LLM)
              </strong>
            </div>
            <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
              Modelo: <strong>{diagnostico.llm_modelo || 'Gemini-1.5-Flash'}</strong>
            </span>
          </div>

          <div
            style={{
              fontSize: '11.5px',
              whiteSpace: 'pre-wrap',
              color: 'var(--text-secondary)',
              lineHeight: 1.45,
              backgroundColor: '#faf5ff',
              padding: '10px 12px',
              borderRadius: '6px',
              border: '1px solid #f3e8ff',
              maxHeight: '120px',
              overflowY: 'auto',
            }}
          >
            {diagnostico.sintesis_llm}
          </div>

          <div
            style={{
              display: 'flex',
              gap: '12px',
              marginTop: '6px',
              paddingTop: '6px',
              borderTop: '1px solid var(--border-color)',
              fontSize: '10.5px',
              color: 'var(--text-muted)',
            }}
          >
            <span>Tokens Entrada: <strong>{diagnostico.tokens_entrada}</strong></span>
            <span>Tokens Salida: <strong>{diagnostico.tokens_salida}</strong></span>
          </div>
        </div>
      )}
    </div>
  );
};
