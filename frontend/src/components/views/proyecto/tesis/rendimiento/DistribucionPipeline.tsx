import React from 'react';
import { Sparkles, Layers } from 'lucide-react';
import { Card } from '../../../../common/Card';
import { Badge } from '../../../../common/Badge';
import type { ResumenMetricas } from '../../../../../types';

interface DistribucionPipelineProps {
  metricas: ResumenMetricas | null;
  totalConsultas: number;
}

const getModoLabel = (modo: string) => {
  switch (modo) {
    case 'completo_ml_rag_llm':
      return 'Pipeline Completo (Linear SVM + RAG + WhatsApp)';
    case 'fallback_ml_rag':
      return 'Inferencia Local ML (SVM + Manuales RAG)';
    case 'degradado_offline':
      return 'Modo Local Offline (Reglas Heurísticas)';
    default:
      return modo;
  }
};

export const DistribucionPipeline: React.FC<DistribucionPipelineProps> = ({
  metricas,
  totalConsultas,
}) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
      {/* Hipótesis de Fallas Frecuentes Generadas */}
      <Card style={{ backgroundColor: '#ffffff', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Sparkles size={16} style={{ color: 'var(--primary)' }} />
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: 'var(--text-main)' }}>
            Hipótesis de Falla Generadas por CarBot
          </h4>
        </div>

        {metricas && metricas.fallas_frecuentes.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {metricas.fallas_frecuentes.slice(0, 5).map((f: { falla: string; cantidad: number }) => (
              <div key={f.falla}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{f.falla}</span>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 700 }}>{f.cantidad} hipótesis</span>
                </div>
                <div style={{ height: '6px', backgroundColor: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      backgroundColor: 'var(--primary)',
                      width: `${Math.min(100, (f.cantidad / Math.max(1, totalConsultas)) * 100)}%`,
                      borderRadius: '4px',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-muted)' }}>
            Sin registros de hipótesis de falla en este período.
          </p>
        )}
      </Card>

      {/* Pipeline de Inferencia en Evaluación Local */}
      <Card style={{ backgroundColor: '#ffffff', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Layers size={16} style={{ color: '#2563eb' }} />
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: 'var(--text-main)' }}>
            Pipeline de Inferencia en Evaluación Local
          </h4>
        </div>

        {metricas && metricas.distribucion_modos.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {metricas.distribucion_modos.map((m: { modo: string; cantidad: number }) => (
              <div
                key={m.modo}
                style={{
                  padding: '8px 12px',
                  borderRadius: '6px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  {getModoLabel(m.modo)}
                </span>
                <Badge type={m.modo} label={`${m.cantidad} consultas`} size="sm" />
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            <p style={{ margin: '0 0 6px 0' }}>
              <strong>Arquitectura:</strong> Linear SVM + TF-IDF para clasificación multiclase de averías vehiculares, asistido por RAG en manuales de taller y fallback a reglas locales/modo degradado.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};
