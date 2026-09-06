import React, { useState } from 'react';
import { Cpu, FileCheck } from 'lucide-react';
import { Modal } from '../../common/Modal';
import type { Diagnostico } from '../../../types';
import {
  DiagnosticoMetaHeader,
  DiagnosticoPipelineStepper,
  DiagnosticoMlSection,
  DiagnosticoRagSection,
  DiagnosticoValidacionPanel,
} from './modal';

export interface DiagnosticoDetalleModalProps {
  diagnostico: Diagnostico | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DiagnosticoDetalleModal: React.FC<DiagnosticoDetalleModalProps> = ({
  diagnostico,
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'diagnostico' | 'trazabilidad'>('diagnostico');

  if (!diagnostico) return null;

  const tienePlaca =
    diagnostico.placa_vehiculo &&
    diagnostico.placa_vehiculo.trim() !== '' &&
    !diagnostico.placa_vehiculo.toLowerCase().includes('sin placa');

  const tituloModal = tienePlaca
    ? `Detalle de Diagnóstico — ${diagnostico.placa_vehiculo}`
    : `Detalle de Diagnóstico #${diagnostico.id ? diagnostico.id.slice(0, 8) : ''}`;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tituloModal}
      maxWidth="840px"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '2px 0' }}>
        {/* Switcher de 2 Sub-pestañas Internas */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            backgroundColor: '#f1f5f9',
            padding: '3px',
            borderRadius: '8px',
            gap: '3px',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('diagnostico')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              padding: '7px 10px',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 700,
              border: 'none',
              backgroundColor: activeTab === 'diagnostico' ? '#ffffff' : 'transparent',
              color: activeTab === 'diagnostico' ? 'var(--primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              boxShadow: activeTab === 'diagnostico' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            <FileCheck size={14} />
            <span>Diagnóstico y Validación</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('trazabilidad')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              padding: '7px 10px',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 700,
              border: 'none',
              backgroundColor: activeTab === 'trazabilidad' ? '#ffffff' : 'transparent',
              color: activeTab === 'trazabilidad' ? 'var(--primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              boxShadow: activeTab === 'trazabilidad' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            <Cpu size={14} />
            <span>Pipeline & ML ({diagnostico.duracion_ms}ms)</span>
          </button>
        </div>

        {/* Tab 1: Diagnóstico y Validación */}
        {activeTab === 'diagnostico' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <DiagnosticoMetaHeader diagnostico={diagnostico} />

            {/* Diagnóstico Predictivo Resumido */}
            <div
              style={{
                backgroundColor: '#f8faff',
                border: '1px solid #dbeafe',
                borderRadius: '10px',
                padding: '12px 14px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#1d4ed8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Falla Diagnosticada por CarBot IA
                </span>
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#059669', backgroundColor: '#ecfdf5', padding: '1px 6px', borderRadius: '4px' }}>
                  {diagnostico.confianza}% Certeza
                </span>
              </div>
              <h3 style={{ margin: '0 0 6px 0', fontSize: '15px', fontWeight: 800, color: '#1e293b' }}>
                {diagnostico.falla_predicha}
              </h3>
              {diagnostico.tiempo_gravedad && (
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {diagnostico.tiempo_gravedad}
                </p>
              )}
            </div>

            {/* Supervisión y Confirmación Técnica */}
            <DiagnosticoValidacionPanel diagnostico={diagnostico} />
          </div>
        )}

        {/* Tab 2: Pipeline y Machine Learning */}
        {activeTab === 'trazabilidad' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <DiagnosticoPipelineStepper diagnostico={diagnostico} />
            <DiagnosticoMlSection diagnostico={diagnostico} />
            <DiagnosticoRagSection diagnostico={diagnostico} />
          </div>
        )}
      </div>
    </Modal>
  );
};
