import React from 'react';
import { Calendar, Car, CheckCircle2, Clock, FileCheck, Phone, User } from 'lucide-react';
import { DiagnosticoValidacionPanel } from './DiagnosticoValidacionPanel';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoTallerPanelProps {
  diagnostico: Diagnostico;
  onCrearPostTest?: (diag: Diagnostico) => void;
  onClose?: () => void;
}

export const DiagnosticoTallerPanel: React.FC<DiagnosticoTallerPanelProps> = ({
  diagnostico,
  onCrearPostTest,
  onClose,
}) => {
  const tienePlaca =
    diagnostico.placa_vehiculo &&
    diagnostico.placa_vehiculo.trim() !== '' &&
    !diagnostico.placa_vehiculo.toLowerCase().includes('sin placa');

  const esTiempoGravedadValido =
    Boolean(diagnostico.tiempo_gravedad) &&
    diagnostico.tiempo_gravedad.trim() !== '' &&
    diagnostico.tiempo_gravedad !== diagnostico.notas_mecanico &&
    !diagnostico.tiempo_gravedad.toLowerCase().includes('se confirma mediante inspección') &&
    !diagnostico.tiempo_gravedad.toLowerCase().includes('se descartan las causas');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* 1. Ficha del Vehículo y Solicitante */}
      <div
        style={{
          backgroundColor: '#f8fafc',
          border: '1px solid var(--border-color)',
          borderRadius: '10px',
          padding: '10px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          fontSize: '11.5px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Car size={14} style={{ color: '#2563eb' }} />
            {tienePlaca ? (
              <span
                style={{
                  display: 'inline-block',
                  border: '2px solid #0f172a',
                  borderRadius: '4px',
                  padding: '1px 7px',
                  fontWeight: 800,
                  fontSize: '12px',
                  letterSpacing: '0.08em',
                  backgroundColor: '#ffffff',
                  color: '#0f172a',
                }}
              >
                {diagnostico.placa_vehiculo}
              </span>
            ) : (
              <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '12px' }}>
                Sin Placa Asignada
              </span>
            )}
          </div>
          <span style={{ color: 'var(--text-muted)', fontSize: '10.5px', fontWeight: 600 }}>
            {diagnostico.marca_modelo && !diagnostico.marca_modelo.toLowerCase().includes('no registrado')
              ? diagnostico.marca_modelo
              : 'Modelo por verificar'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-secondary)', borderTop: '1px solid #e2e8f0', paddingTop: '5px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <User size={12} style={{ color: 'var(--text-muted)' }} />
            <span>{diagnostico.mecanico_nombre || diagnostico.cliente_nombre || 'Mecánico'}</span>
          </div>
          {diagnostico.cliente_telefono && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10.5px' }}>
              <Phone size={10} />
              <span>{diagnostico.cliente_telefono}</span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)', fontSize: '10.5px' }}>
          <Calendar size={11} />
          <span>{diagnostico.fecha_hora}</span>
        </div>
      </div>

      {/* 2. Hipótesis Diagnosticada por CarBot */}
      <div
        style={{
          backgroundColor: '#f8faff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          padding: '8px 12px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
          <span style={{ fontSize: '9.5px', fontWeight: 800, color: '#1d4ed8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Hipótesis CarBot IA
          </span>
          <span style={{ fontSize: '10px', fontWeight: 800, color: '#059669', backgroundColor: '#ecfdf5', padding: '1px 6px', borderRadius: '4px', border: '1px solid #a7f3d0' }}>
            {diagnostico.confianza}% Certeza
          </span>
        </div>
        <div style={{ fontSize: '12.5px', fontWeight: 800, color: '#0f172a' }}>
          {diagnostico.falla_predicha}
        </div>
      </div>

      {/* 3. Estimación de Reparación y Gravedad (si no es duplicado) */}
      {esTiempoGravedadValido && (
        <div
          style={{
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: '8px',
            padding: '8px 12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
            fontSize: '11px',
            color: '#92400e',
          }}
        >
          <Clock size={13} style={{ color: '#d97706', marginTop: '1px', flexShrink: 0 }} />
          <div>
            <strong>Estimación de Taller:</strong>
            <div style={{ marginTop: '1px', lineHeight: 1.3 }}>{diagnostico.tiempo_gravedad}</div>
          </div>
        </div>
      )}

      {/* 4. Supervisión y Validación Física en Taller */}
      <DiagnosticoValidacionPanel diagnostico={diagnostico} />

      {/* 5. Botón de acción: Crear/Vincular a Ficha Oficial Post-test */}
      {onCrearPostTest && (
        <button
          type="button"
          onClick={() => {
            onCrearPostTest(diagnostico);
            if (onClose) onClose();
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '9px 12px',
            backgroundColor: '#1d4ed8',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(29,78,216,0.25)',
            transition: 'background-color 0.15s ease',
          }}
        >
          <FileCheck size={15} />
          <span>+ Crear registro Post-test oficial</span>
        </button>
      )}

      {/* 6. Tarjeta de Trazabilidad con Indicadores de Tesis */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderRadius: '10px',
          padding: '8px 12px',
          fontSize: '10.5px',
        }}
      >
        <div style={{ fontWeight: 700, color: 'var(--text-main)', marginBottom: '3px' }}>
          📐 Operacionalización de Tesis (Anexo 1 UCV):
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={11} style={{ color: '#16a34a' }} />
            <span><strong>Ind. 1:</strong> Síntoma registrado correctamente</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={11} style={{ color: '#16a34a' }} />
            <span><strong>Ind. 2:</strong> Pipeline 3 etapas procesado</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ fontSize: '10px' }}>⚖️</span>
            <span><strong>Ind. 3:</strong> Exactitud ML contrastada en taller</span>
          </div>
        </div>
      </div>
    </div>
  );
};
