import React from 'react';

interface DiagnosticosHeaderProps {
  totalProcesados: number;
  totalTotal: number;
}

export const DiagnosticosHeader: React.FC<DiagnosticosHeaderProps> = ({
  totalProcesados,
  totalTotal,
}) => (
  <div>
    <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
      Historial de diagnósticos
    </h2>
    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
      Mostrando <strong>{totalProcesados}</strong> de {totalTotal} registros
    </span>
  </div>
);
