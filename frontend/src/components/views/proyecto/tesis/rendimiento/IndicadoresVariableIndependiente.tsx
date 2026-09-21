import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';
import { Card } from '../../../../common/Card';
import type { IndicadoresVIResult } from './calculosIndicadores';

interface IndicadoresVariableIndependienteProps {
  indicadores: IndicadoresVIResult;
}

export const IndicadoresVariableIndependiente: React.FC<IndicadoresVariableIndependienteProps> = ({
  indicadores,
}) => {
  const {
    pctSintomas,
    pctProcesamiento,
    exactitudModelo,
    esMedicionPendiente,
    casosVerificados,
    notaMetodologica,
  } = indicadores;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldCheck size={16} style={{ color: 'var(--primary)' }} />
          <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Indicadores de la Variable Independiente (Matriz de Operacionalización)
          </h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11.5px', color: esMedicionPendiente ? '#b45309' : '#047857' }}>
          <Info size={13} />
          <span>{notaMetodologica} ({casosVerificados} verificados)</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        {/* Indicador VI 1: % Síntomas registrados correctamente */}
        <Card style={{ padding: '16px', borderLeft: '4px solid var(--primary)', backgroundColor: '#ffffff' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            Indicador 1 · Registro de Síntomas
          </span>
          <div
            style={{
              fontSize: esMedicionPendiente ? '20px' : '26px',
              fontWeight: 800,
              color: esMedicionPendiente ? '#64748b' : 'var(--text-main)',
              marginTop: '6px',
            }}
          >
            {pctSintomas}
          </div>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--primary)', marginTop: '2px' }}>
            % Síntomas registrados correctamente
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '6px 0 0 0', lineHeight: '1.35' }}>
            Criterio: Relato original en WhatsApp contrastado con el registro estructurado y validado por el responsable en taller.
          </p>
        </Card>

        {/* Indicador VI 2: % Datos procesados correctamente */}
        <Card style={{ padding: '16px', borderLeft: '4px solid #2563eb', backgroundColor: '#ffffff' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            Indicador 2 · Procesamiento de Datos
          </span>
          <div
            style={{
              fontSize: esMedicionPendiente ? '20px' : '26px',
              fontWeight: 800,
              color: esMedicionPendiente ? '#64748b' : '#2563eb',
              marginTop: '6px',
            }}
          >
            {pctProcesamiento}
          </div>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#1d4ed8', marginTop: '2px' }}>
            % Datos procesados correctamente
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '6px 0 0 0', lineHeight: '1.35' }}>
            Criterio: Casos que completan con éxito las 3 etapas (normalización, extracción técnica y clasificación) verificadas.
          </p>
        </Card>

        {/* Indicador VI 3: Exactitud del modelo (Accuracy físico) */}
        <Card style={{ padding: '16px', borderLeft: '4px solid #059669', backgroundColor: '#ffffff' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            Indicador 3 · Exactitud del Modelo
          </span>
          <div
            style={{
              fontSize: esMedicionPendiente ? '20px' : '26px',
              fontWeight: 800,
              color: esMedicionPendiente ? '#64748b' : '#059669',
              marginTop: '6px',
            }}
          >
            {exactitudModelo}
          </div>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#047857', marginTop: '2px' }}>
            Exactitud (Accuracy) validada en taller
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '6px 0 0 0', lineHeight: '1.35' }}>
            Criterio: Predicciones del modelo Linear SVM coincidentes con la falla confirmada físicamente mediante evidencia en taller.
          </p>
        </Card>
      </div>
    </div>
  );
};
