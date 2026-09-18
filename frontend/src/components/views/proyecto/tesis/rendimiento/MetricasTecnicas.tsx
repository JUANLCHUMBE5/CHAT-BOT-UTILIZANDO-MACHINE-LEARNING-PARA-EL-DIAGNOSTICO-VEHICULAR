import React from 'react';
import { Cpu, Clock, MessageSquare, CheckCircle } from 'lucide-react';
import { Card } from '../../../../common/Card';
import type { TelemetriaTecnicaResult } from './calculosIndicadores';

interface MetricasTecnicasProps {
  telemetria: TelemetriaTecnicaResult;
  confirmadosCount: number;
  pendientesCount: number;
}

export const MetricasTecnicas: React.FC<MetricasTecnicasProps> = ({
  telemetria,
  confirmadosCount,
  pendientesCount,
}) => {
  const {
    tiempoInferenciaMlTexto,
    tiempoTotalPipelineTexto,
    tiempoTotalSegundosTexto,
    totalConsultas,
  } = telemetria;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
        <Cpu size={16} style={{ color: '#64748b' }} />
        <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Métricas Técnicas y Tiempos de Respuesta Reales
        </h3>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {/* Tiempo de Inferencia ML */}
        <Card style={{ padding: '14px', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
              Tiempo Inferencia ML (SVM)
            </span>
            <Clock size={15} style={{ color: '#2563eb' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', marginTop: '6px' }}>
            {tiempoInferenciaMlTexto}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', display: 'block' }}>
            Vectorización TF-IDF + Linear SVM
          </span>
        </Card>

        {/* Tiempo Total de Respuesta WhatsApp */}
        <Card style={{ padding: '14px', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
              Tiempo Total Pipeline WhatsApp
            </span>
            <Clock size={15} style={{ color: 'var(--primary)' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', marginTop: '6px' }}>
            {tiempoTotalPipelineTexto}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', display: 'block' }}>
            {tiempoTotalSegundosTexto}
          </span>
        </Card>

        {/* Consultas procesadas por WhatsApp */}
        <Card style={{ padding: '14px', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
              Consultas Procesadas
            </span>
            <MessageSquare size={15} style={{ color: 'var(--primary)' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', marginTop: '6px' }}>
            {totalConsultas}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', display: 'block' }}>
            Exclusivamente canal WhatsApp
          </span>
        </Card>

        {/* Casos Confirmados vs Pendientes */}
        <Card style={{ padding: '14px', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
              Confirmadas vs Pendientes
            </span>
            <CheckCircle size={15} style={{ color: '#059669' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#059669', marginTop: '6px' }}>
            {confirmadosCount} <span style={{ fontSize: '13px', color: '#d97706', fontWeight: 600 }}>/ {pendientesCount} pend.</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', display: 'block' }}>
            Validación física por mecánicos
          </span>
        </Card>
      </div>
    </div>
  );
};
