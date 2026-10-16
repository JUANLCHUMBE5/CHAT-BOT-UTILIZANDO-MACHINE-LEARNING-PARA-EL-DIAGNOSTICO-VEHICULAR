import React from 'react';
import { Car, Cpu, ShieldAlert } from 'lucide-react';
import type { MensajeLabResponse, ComprobacionResult } from '../../../services/api';

interface LaboratorioPanelProps {
  estado: MensajeLabResponse | null;
}

export const LaboratorioPanel: React.FC<LaboratorioPanelProps> = ({ estado }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        overflowY: 'auto',
      }}
    >
      {/* Tarjeta: Contexto y Memoria Activa */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Car size={16} color="#2563eb" />
          <h2 style={{ fontSize: '14px', fontWeight: 700, margin: 0, color: '#111827' }}>
            Contexto y Memoria Activa
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', fontSize: '12px' }}>
          <div>
            <span style={{ color: '#6b7280' }}>Placa:</span>{' '}
            <span style={{ fontWeight: 700, color: '#111827' }}>
              {estado?.placa ? (
                <span style={{ background: '#e0e7ff', color: '#3730a3', padding: '2px 6px', borderRadius: '4px' }}>
                  {estado.placa}
                </span>
              ) : (
                '—'
              )}
            </span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Vehículo:</span>{' '}
            <span style={{ fontWeight: 600, color: '#111827' }}>
              {estado?.vehiculo || '—'}
            </span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Case ID:</span>{' '}
            <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#4b5563' }}>
              {estado?.case_id?.slice(0, 8) || '—'}
            </span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Fase:</span>{' '}
            <span style={{ fontWeight: 600, color: '#0d9488' }}>
              {estado?.fase || 'inicio'}
            </span>
          </div>
        </div>

        <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11.5px' }}>
          <div>
            <span style={{ color: '#059669', fontWeight: 600 }}>Síntomas confirmados:</span>{' '}
            {estado?.sintomas_confirmados && estado.sintomas_confirmados.length > 0 ? (
              estado.sintomas_confirmados.map((s, i) => (
                <span key={i} style={{ background: '#ecfdf5', color: '#047857', padding: '1px 6px', borderRadius: '4px', marginRight: '4px' }}>
                  ✓ {s}
                </span>
              ))
            ) : (
              <span style={{ color: '#9ca3af' }}>Ninguno</span>
            )}
          </div>

          <div>
            <span style={{ color: '#dc2626', fontWeight: 600 }}>Síntomas negados:</span>{' '}
            {estado?.sintomas_negados && estado.sintomas_negados.length > 0 ? (
              estado.sintomas_negados.map((s, i) => (
                <span key={i} style={{ background: '#fef2f2', color: '#b91c1c', padding: '1px 6px', borderRadius: '4px', marginRight: '4px' }}>
                  ✕ {s}
                </span>
              ))
            ) : (
              <span style={{ color: '#9ca3af' }}>Ninguno</span>
            )}
          </div>

          <div>
            <span style={{ color: '#d97706', fontWeight: 600 }}>Limitaciones de herramientas:</span>{' '}
            {estado?.limitaciones && estado.limitaciones.length > 0 ? (
              estado.limitaciones.map((l, i) => (
                <span key={i} style={{ background: '#fffbeb', color: '#b45309', padding: '1px 6px', borderRadius: '4px', marginRight: '4px' }}>
                  ⚠️ {l}
                </span>
              ))
            ) : (
              <span style={{ color: '#9ca3af' }}>Ninguna</span>
            )}
          </div>
        </div>
      </div>

      {/* Tarjeta: Inferencia ML & RAG */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Cpu size={16} color="#7c3aed" />
          <h2 style={{ fontSize: '14px', fontWeight: 700, margin: 0, color: '#111827' }}>
            Inferencia Machine Learning & RAG
          </h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#6b7280' }}>Hipótesis ML (Linear SVM):</span>
            <span style={{ fontWeight: 700, color: '#111827' }}>
              {estado?.diagnostico_ml || 'Pendiente de síntomas'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#6b7280' }}>Confianza Calibrada SVM:</span>
            <span style={{ fontWeight: 600, color: '#7c3aed' }}>
              {estado?.diagnostico_ml?.includes('No aplica') || estado?.modo_diagnostico === 'memoria_tecnica'
                ? 'No aplica'
                : estado?.confianza_ml
                ? `${(estado.confianza_ml * 100).toFixed(1)}% (SVM)`
                : '—'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#6b7280' }}>Procedimiento RAG OEM:</span>
            <span style={{ fontWeight: 600, color: '#0d9488' }}>
              {estado?.titulo_manual || 'Corpus no requerido'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#6b7280' }}>Similitud Coseno FAISS:</span>
            <span style={{ fontWeight: 600, color: '#4b5563' }}>
              {estado?.similitud_rag ? `${(estado.similitud_rag * 100).toFixed(1)}%` : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Tarjeta: Comprobaciones Automáticas */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: '12px',
          padding: '16px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
          flex: 1,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <ShieldAlert size={16} color="#059669" />
          <h2 style={{ fontSize: '14px', fontWeight: 700, margin: 0, color: '#111827' }}>
            Comprobaciones Automáticas de Calidad
          </h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {estado?.comprobaciones && estado.comprobaciones.length > 0 ? (
            estado.comprobaciones.map((c: ComprobacionResult, i: number) => (
              <div
                key={i}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: c.resultado === 'APROBADO' ? '#f0fdf4' : c.resultado === 'FALLIDO' ? '#fef2f2' : '#f9fafb',
                  border: `1px solid ${c.resultado === 'APROBADO' ? '#bbf7d0' : c.resultado === 'FALLIDO' ? '#fecaca' : '#e5e7eb'}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: '#1f2937' }}>
                    {c.criterio}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: c.resultado === 'APROBADO' ? '#22c55e' : c.resultado === 'FALLIDO' ? '#ef4444' : '#9ca3af',
                      color: '#ffffff',
                    }}
                  >
                    {c.resultado}
                  </span>
                </div>
                <span style={{ fontSize: '11px', color: '#4b5563' }}>
                  {c.evidencia}
                </span>
              </div>
            ))
          ) : (
            <div style={{ fontSize: '12px', color: '#9ca3af', textAlign: 'center', padding: '20px' }}>
              Sin comprobaciones registradas en el turno actual.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
