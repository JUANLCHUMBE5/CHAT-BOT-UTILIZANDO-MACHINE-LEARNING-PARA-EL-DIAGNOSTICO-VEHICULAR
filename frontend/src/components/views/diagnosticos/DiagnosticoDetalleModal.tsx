import React, { useState } from 'react';
import { FileText, MessageSquare, Wrench } from 'lucide-react';
import { Modal } from '../../common/Modal';
import { Badge } from '../../common/Badge';
import type { Diagnostico } from '../../../types';
import {
  DiagnosticoPipelineStepper,
  DiagnosticoMlSection,
  DiagnosticoRagSection,
  DiagnosticoValidacionPanel,
  DiagnosticoChatWhatsApp,
} from './modal';

export interface DiagnosticoDetalleModalProps {
  diagnostico: Diagnostico | null;
  isOpen: boolean;
  onClose: () => void;
  onCrearPostTest?: (diag: Diagnostico) => void;
}

export const DiagnosticoDetalleModal: React.FC<DiagnosticoDetalleModalProps> = ({
  diagnostico,
  isOpen,
  onClose,
  onCrearPostTest,
}) => {
  const [tabActiva, setTabActiva] = useState<'tecnico' | 'conversacion'>('tecnico');

  if (!diagnostico) return null;

  const tienePlaca =
    diagnostico.placa_vehiculo &&
    diagnostico.placa_vehiculo.trim() !== '' &&
    !diagnostico.placa_vehiculo.toLowerCase().includes('sin placa');

  const tituloModal = tienePlaca
    ? `Diagnóstico ${diagnostico.placa_vehiculo} · ${diagnostico.marca_modelo || 'Vehículo'}`
    : `Diagnóstico #${diagnostico.id ? diagnostico.id.slice(0, 8) : 'Consulta'}`;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tituloModal}
      maxWidth="1100px"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Barra superior de pestañas del modal y metadatos */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '10px',
            padding: '8px 12px',
            backgroundColor: '#f8fafc',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              type="button"
              onClick={() => setTabActiva('tecnico')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 700,
                border: '1px solid',
                borderColor: tabActiva === 'tecnico' ? 'var(--primary)' : 'var(--border-color)',
                backgroundColor: tabActiva === 'tecnico' ? '#fff7ed' : '#ffffff',
                color: tabActiva === 'tecnico' ? 'var(--primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <FileText size={14} />
              <span>Diagnóstico Técnico (A-E)</span>
            </button>
            <button
              type="button"
              onClick={() => setTabActiva('conversacion')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 700,
                border: '1px solid',
                borderColor: tabActiva === 'conversacion' ? '#16a34a' : 'var(--border-color)',
                backgroundColor: tabActiva === 'conversacion' ? '#f0fdf4' : '#ffffff',
                color: tabActiva === 'conversacion' ? '#166534' : 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <MessageSquare size={14} />
              <span>Trazabilidad WhatsApp (F)</span>
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
              Latencia: <strong>{diagnostico.duracion_ms || 0} ms</strong>
            </span>
            <Badge type={diagnostico.estado} />
          </div>
        </div>

        {/* TAB 1: ESTRUCTURA TÉCNICA A-E */}
        {tabActiva === 'tecnico' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* A. IDENTIFICACIÓN */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '12px',
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                padding: '12px 14px',
              }}
            >
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>ID Diagnóstico</div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--text-main)', fontFamily: 'monospace' }}>
                  {diagnostico.id || 'N/A'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>Fecha / Hora</div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--text-main)' }}>
                  {diagnostico.fecha_hora || 'N/A'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>Mecánico / Solicitante</div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--text-main)' }}>
                  {diagnostico.mecanico_nombre || diagnostico.cliente_nombre || 'Mecánico'}
                </div>
                {diagnostico.cliente_telefono && (
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {diagnostico.cliente_telefono}
                  </div>
                )}
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>Vehículo</div>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: tienePlaca ? 'var(--primary)' : 'var(--text-main)' }}>
                  {tienePlaca ? diagnostico.placa_vehiculo : 'Sin placa'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {diagnostico.marca_modelo || 'Consulta general'}
                </div>
              </div>
            </div>

            {/* B. SÍNTOMA REPORTADO */}
            <div
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                padding: '12px 14px',
              }}
            >
              <div style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                B. Síntoma Reportado por el Mecánico
              </div>
              <div
                style={{
                  fontSize: '13px',
                  color: 'var(--text-main)',
                  backgroundColor: '#f8fafc',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0',
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {diagnostico.sintoma_original || 'No se registró texto de síntoma.'}
              </div>
            </div>

            {/* C. PREDICCIÓN CARBOT & D. PROCEDIMIENTO */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '14px',
              }}
            >
              {/* C. PREDICCIÓN CARBOT */}
              <div>
                <DiagnosticoMlSection diagnostico={diagnostico} />
              </div>

              {/* D. PROCEDIMIENTO / EVIDENCIA RAG */}
              <div>
                <DiagnosticoRagSection diagnostico={diagnostico} />
              </div>
            </div>

            {/* E. RESULTADO (Generado / Confirmado / Descartado) */}
            <div>
              <div style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                E. Resultado y Validación de Taller
              </div>
              <DiagnosticoValidacionPanel diagnostico={diagnostico} />
            </div>

            {/* Trazabilidad de Pipeline */}
            <div>
              <div style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Trazabilidad del Pipeline de Inferencia
              </div>
              <DiagnosticoPipelineStepper diagnostico={diagnostico} />
            </div>

            {/* Acción opcional de tesis (solo si se invoca desde el módulo de tesis) */}
            {onCrearPostTest && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => {
                    onCrearPostTest(diagnostico);
                    onClose();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 14px',
                    backgroundColor: '#1d4ed8',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '12.5px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  <Wrench size={15} />
                  <span>Vincular a Ficha Post-test de Tesis</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: F. TRAZABILIDAD CONVERSACIONAL REAL */}
        {tabActiva === 'conversacion' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Historial cronológico de la interacción para auditoría de preguntas y respuestas entre el mecánico y CarBot.
            </div>
            <DiagnosticoChatWhatsApp diagnostico={diagnostico} />
          </div>
        )}
      </div>
    </Modal>
  );
};
