import React from 'react';
import { Award, TrendingUp } from 'lucide-react';
import { Card } from '../../../common/Card';

interface TesisFichaOverviewCardProps {
  infoFicha: {
    codigo: string;
    numero: string;
    dimension: string;
    indicador: string;
    formula: string;
    preValor: string;
    postValor: string;
    preDetalle: string;
    postDetalle: string;
    mejora: string;
    hipotesis: string;
  };
}

export const TesisFichaOverviewCard: React.FC<TesisFichaOverviewCardProps> = ({
  infoFicha,
}) => {
  return (
    <Card style={{ backgroundColor: '#ffffff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
        <div>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#3b82f6', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {infoFicha.codigo}
          </span>
          <h4 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0 0 0' }}>
            {infoFicha.numero}
          </h4>
        </div>
        <span
          style={{
            fontSize: '12px',
            fontWeight: 700,
            padding: '4px 12px',
            borderRadius: '20px',
            backgroundColor: '#dcfce7',
            color: '#15803d',
            border: '1px solid #bbf7d0',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <TrendingUp size={14} />
          {infoFicha.mejora}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', fontSize: '12px', marginBottom: '14px' }}>
        <div>
          <strong style={{ color: 'var(--text-secondary)' }}>Dimensión: </strong>
          <span style={{ color: 'var(--text-main)' }}>{infoFicha.dimension}</span>
        </div>
        <div>
          <strong style={{ color: 'var(--text-secondary)' }}>Indicador: </strong>
          <span style={{ color: 'var(--text-main)' }}>{infoFicha.indicador}</span>
        </div>
      </div>

      <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-main)', borderRadius: '8px', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px', border: '1px solid var(--border-color)' }}>
        <strong style={{ color: 'var(--text-main)' }}>Fórmula: </strong>
        <code>{infoFicha.formula}</code>
      </div>

      {/* Resultados Pre vs Post */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div style={{ padding: '14px', borderRadius: '10px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Pre-test (Diagnóstico Manual)
          </span>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#334155', marginTop: '4px' }}>
            {infoFicha.preValor}
          </div>
          <span style={{ fontSize: '11px', color: '#64748b', marginTop: '2px', display: 'block' }}>
            {infoFicha.preDetalle}
          </span>
        </div>

        <div style={{ padding: '14px', borderRadius: '10px', backgroundColor: '#eff6ff', border: '1px solid #bfdbfe' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#1d4ed8', textTransform: 'uppercase' }}>
            Post-test (Asistido por CarBot AI)
          </span>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#1e40af', marginTop: '4px' }}>
            {infoFicha.postValor}
          </div>
          <span style={{ fontSize: '11px', color: '#2563eb', marginTop: '2px', display: 'block' }}>
            {infoFicha.postDetalle}
          </span>
        </div>
      </div>

      <div style={{ marginTop: '12px', fontSize: '12px', color: '#059669', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Award size={16} />
        <span>{infoFicha.hipotesis}</span>
      </div>
    </Card>
  );
};
