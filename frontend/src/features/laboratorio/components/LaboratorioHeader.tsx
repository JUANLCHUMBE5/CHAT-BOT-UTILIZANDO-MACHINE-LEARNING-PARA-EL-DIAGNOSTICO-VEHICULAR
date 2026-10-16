import React from 'react';
import { Play, RotateCcw, Download } from 'lucide-react';

interface LaboratorioHeaderProps {
  cargando: boolean;
  casoEnEjecucion: string | null;
  tieneHistorial: boolean;
  onReproducirCaso: (caso: 'toyota' | 'nissan') => void;
  onReiniciar: () => void;
  onExportarJson: () => void;
}

export const LaboratorioHeader: React.FC<LaboratorioHeaderProps> = ({
  cargando,
  casoEnEjecucion,
  tieneHistorial,
  onReproducirCaso,
  onReiniciar,
  onExportarJson,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
        background: 'var(--surface-card, #ffffff)',
        padding: '16px 20px',
        borderRadius: '12px',
        border: '1px solid var(--border-color, #e5e7eb)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0, color: 'var(--text-primary, #111827)' }}>
            Laboratorio de Pruebas CarBot
          </h1>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              padding: '3px 8px',
              borderRadius: '6px',
              background: '#dcfce7',
              color: '#166534',
              border: '1px solid #bbf7d0',
            }}
          >
            Motor Inferencia Real
          </span>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              padding: '3px 8px',
              borderRadius: '6px',
              background: '#fef3c7',
              color: '#92400e',
              border: '1px solid #fde68a',
            }}
          >
            PostgreSQL Aislado
          </span>
        </div>
        <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-secondary, #6b7280)' }}>
          Ejecución conversacional directa sin Meta WhatsApp. Diagnóstico SVM jerárquico + RAG de taller.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button
          onClick={() => onReproducirCaso('toyota')}
          disabled={cargando}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            background: '#2563eb',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: cargando ? 'not-allowed' : 'pointer',
            opacity: cargando ? 0.7 : 1,
          }}
        >
          <Play size={14} />
          {casoEnEjecucion === 'toyota' ? 'Reproduciendo...' : 'Caso Toyota Yaris (ABC-123)'}
        </button>

        <button
          onClick={() => onReproducirCaso('nissan')}
          disabled={cargando}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            background: '#0d9488',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: cargando ? 'not-allowed' : 'pointer',
            opacity: cargando ? 0.7 : 1,
          }}
        >
          <Play size={14} />
          {casoEnEjecucion === 'nissan' ? 'Reproduciendo...' : 'Caso Nissan Sentra (XYZ-789)'}
        </button>

        <button
          onClick={onReiniciar}
          disabled={cargando}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            background: 'transparent',
            color: 'var(--text-primary, #374151)',
            border: '1px solid var(--border-color, #d1d5db)',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 500,
            cursor: cargando ? 'not-allowed' : 'pointer',
          }}
        >
          <RotateCcw size={14} />
          Reiniciar
        </button>

        <button
          onClick={onExportarJson}
          disabled={!tieneHistorial}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            background: 'transparent',
            color: 'var(--text-primary, #374151)',
            border: '1px solid var(--border-color, #d1d5db)',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 500,
            cursor: !tieneHistorial ? 'not-allowed' : 'pointer',
            opacity: !tieneHistorial ? 0.5 : 1,
          }}
        >
          <Download size={14} />
          Exportar JSON
        </button>
      </div>
    </div>
  );
};
