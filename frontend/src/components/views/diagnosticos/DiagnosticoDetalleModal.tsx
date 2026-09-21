import React, { useState } from 'react';
import { Cpu, FileCheck, LayoutGrid, Layers, MessageSquare } from 'lucide-react';
import { Modal } from '../../common/Modal';
import { Badge } from '../../common/Badge';
import type { Diagnostico } from '../../../types';
import {
  DiagnosticoMetaHeader,
  DiagnosticoPipelineStepper,
  DiagnosticoMlSection,
  DiagnosticoRagSection,
  DiagnosticoValidacionPanel,
  DiagnosticoChatWhatsApp,
  DiagnosticoTallerPanel,
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
  const [viewMode, setViewMode] = useState<'panoramica' | 'pestanas'>('panoramica');
  const [activeTab, setActiveTab] = useState<'chat' | 'procesamiento' | 'validacion'>('chat');

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
      maxWidth="1420px"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* Barra superior unificada: Selector de vista y metadatos clave */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px',
            padding: '6px 12px',
            backgroundColor: '#f8fafc',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Distribución:
            </span>
            <button
              type="button"
              onClick={() => setViewMode('panoramica')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '5px 10px',
                borderRadius: '6px',
                fontSize: '11.5px',
                fontWeight: 700,
                border: '1px solid',
                borderColor: viewMode === 'panoramica' ? '#2563eb' : 'var(--border-color)',
                backgroundColor: viewMode === 'panoramica' ? '#eff6ff' : '#ffffff',
                color: viewMode === 'panoramica' ? '#1d4ed8' : 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <LayoutGrid size={13} />
              <span>Panorámica Web (X | X | X)</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('pestanas')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '5px 10px',
                borderRadius: '6px',
                fontSize: '11.5px',
                fontWeight: 700,
                border: '1px solid',
                borderColor: viewMode === 'pestanas' ? '#2563eb' : 'var(--border-color)',
                backgroundColor: viewMode === 'pestanas' ? '#eff6ff' : '#ffffff',
                color: viewMode === 'pestanas' ? '#1d4ed8' : 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <Layers size={13} />
              <span>Por Pestañas</span>
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              Mecánico: <strong>{diagnostico.mecanico_nombre || 'Taller'}</strong> · Latencia total: <strong>{diagnostico.duracion_ms} ms</strong>
            </span>
            <Badge type={diagnostico.estado} />
          </div>
        </div>

        {/* MODO 1: VISTA PANORÁMICA EQUILIBRADA (X | X | X) */}
        {viewMode === 'panoramica' ? (
          <div className="diagnostico-modal-grid">
            {/* ================= COLUMNA 1: CHAT WHATSAPP ================= */}
            <div className="diagnostico-modal-col">
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '6px 10px',
                  backgroundColor: '#f0fdf4',
                  borderRadius: '6px',
                  border: '1px solid #bbf7d0',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <MessageSquare size={13} style={{ color: '#16a34a' }} />
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#166534', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    1. Chat WhatsApp (Pregunta y Devolución)
                  </span>
                </div>
                <span style={{ fontSize: '9.5px', color: '#15803d', fontWeight: 700 }}>
                  Canal Webhook
                </span>
              </div>

              <DiagnosticoChatWhatsApp diagnostico={diagnostico} />
            </div>

            {/* ================= COLUMNA 2: PROCESAMIENTO IA (ML + RAG + LLM) ================= */}
            <div className="diagnostico-modal-col">
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '6px 10px',
                  backgroundColor: '#eff6ff',
                  borderRadius: '6px',
                  border: '1px solid #bfdbfe',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Cpu size={13} style={{ color: '#2563eb' }} />
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#1e40af', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    2. Procesamiento del Sistema (Pipeline IA)
                  </span>
                </div>
                <span style={{ fontSize: '10px', fontWeight: 700, color: '#1d4ed8' }}>
                  {diagnostico.duracion_ms} ms
                </span>
              </div>

              <DiagnosticoPipelineStepper diagnostico={diagnostico} />
              <DiagnosticoMlSection diagnostico={diagnostico} />
              <DiagnosticoRagSection diagnostico={diagnostico} />
            </div>

            {/* ================= COLUMNA 3: TALLER, VALIDACIÓN & TESIS ================= */}
            <div className="diagnostico-modal-col">
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '6px 10px',
                  backgroundColor: '#faf5ff',
                  borderRadius: '6px',
                  border: '1px solid #e9d5ff',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <FileCheck size={13} style={{ color: '#7c3aed' }} />
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#6b21a8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    3. Taller & Ficha Oficial Post-test
                  </span>
                </div>
                <span style={{ fontSize: '9.5px', color: '#7c3aed', fontWeight: 700 }}>
                  Anexo 2 UCV
                </span>
              </div>

              <DiagnosticoTallerPanel
                diagnostico={diagnostico}
                onCrearPostTest={onCrearPostTest}
                onClose={onClose}
              />
            </div>
          </div>
        ) : (
          /* MODO 2: VISTA POR PESTAÑAS TRADICIONAL */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                backgroundColor: '#f1f5f9',
                padding: '3px',
                borderRadius: '8px',
                gap: '3px',
              }}
            >
              <button
                type="button"
                onClick={() => setActiveTab('chat')}
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
                  backgroundColor: activeTab === 'chat' ? '#ffffff' : 'transparent',
                  color: activeTab === 'chat' ? 'var(--primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  boxShadow: activeTab === 'chat' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                <MessageSquare size={14} />
                <span>Chat WhatsApp</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('procesamiento')}
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
                  backgroundColor: activeTab === 'procesamiento' ? '#ffffff' : 'transparent',
                  color: activeTab === 'procesamiento' ? 'var(--primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  boxShadow: activeTab === 'procesamiento' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                <Cpu size={14} />
                <span>Pipeline & ML ({diagnostico.duracion_ms}ms)</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('validacion')}
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
                  backgroundColor: activeTab === 'validacion' ? '#ffffff' : 'transparent',
                  color: activeTab === 'validacion' ? 'var(--primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  boxShadow: activeTab === 'validacion' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                <FileCheck size={14} />
                <span>Validación Taller</span>
              </button>
            </div>

            {activeTab === 'chat' && <DiagnosticoChatWhatsApp diagnostico={diagnostico} />}

            {activeTab === 'procesamiento' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <DiagnosticoPipelineStepper diagnostico={diagnostico} />
                <DiagnosticoMlSection diagnostico={diagnostico} />
                <DiagnosticoRagSection diagnostico={diagnostico} />
              </div>
            )}

            {activeTab === 'validacion' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <DiagnosticoMetaHeader diagnostico={diagnostico} />
                {onCrearPostTest && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
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
                      <FileCheck size={15} />
                      <span>Crear registro Post-test</span>
                    </button>
                  </div>
                )}
                <DiagnosticoValidacionPanel diagnostico={diagnostico} />
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
};
