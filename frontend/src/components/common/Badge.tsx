import React from 'react';

type BadgeType =
  | 'generado'
  | 'en_revision'
  | 'confirmado'
  | 'descartado'
  | 'completo_ml_rag_llm'
  | 'diagnostico_degradado_ml_rag'
  | 'en_cola_gemini'
  | 'saludo'
  | 'baja_confianza'
  | 'activo'
  | 'bloqueado';

interface BadgeProps {
  type: BadgeType | string;
  label?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ type, label, size = 'md' }) => {
  const getStylesAndText = (): { bg: string; color: string; text: string } => {
    switch (type) {
      case 'confirmado':
      case 'activo':
        return { bg: 'var(--status-success-bg)', color: 'var(--status-success-text)', text: label || 'Confirmado' };
      case 'en_revision':
      case 'en_cola_gemini':
      case 'baja_confianza':
        return { bg: 'var(--status-warning-bg)', color: 'var(--status-warning-text)', text: label || (type === 'en_cola_gemini' ? 'En Cola' : 'En Revisión') };
      case 'descartado':
      case 'bloqueado':
        return { bg: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', text: label || (type === 'bloqueado' ? 'Bloqueado' : 'Descartado') };
      case 'generado':
      case 'completo_ml_rag_llm':
        return { bg: '#fff7ed', color: '#c2410c', text: label || (type === 'completo_ml_rag_llm' ? 'ML+RAG+LLM' : 'Generado') };
      case 'diagnostico_degradado_ml_rag':
        return { bg: '#f1f5f9', color: '#475569', text: label || 'Degradado (ML+RAG)' };
      case 'saludo':
        return { bg: '#e0f2fe', color: '#0369a1', text: label || 'Saludo' };
      default:
        return { bg: 'var(--bg-subtle)', color: 'var(--text-secondary)', text: label || type };
    }
  };

  const { bg, color, text } = getStylesAndText();

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: size === 'sm' ? '2px 8px' : '4px 10px',
        fontSize: size === 'sm' ? '11px' : '12px',
        fontWeight: 600,
        borderRadius: '9999px',
        backgroundColor: bg,
        color: color,
        whiteSpace: 'nowrap',
      }}
    >
      {text}
    </span>
  );
};
