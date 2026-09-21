import React from 'react';
import { AlertTriangle, CheckCircle2, Clock3, XCircle } from 'lucide-react';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoValidacionPanelProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoValidacionPanel: React.FC<DiagnosticoValidacionPanelProps> = ({
  diagnostico,
}) => {
  const confirmado = diagnostico.estado === 'confirmado';
  const descartado = diagnostico.estado === 'descartado';
  const enRevision = diagnostico.estado === 'en_revision';
  const color = confirmado ? '#047857' : descartado ? '#be123c' : '#b45309';
  const fondo = confirmado ? '#ecfdf5' : descartado ? '#fff1f2' : '#fffbeb';
  const borde = confirmado ? '#a7f3d0' : descartado ? '#fecdd3' : '#fde68a';
  const Icono = confirmado
    ? CheckCircle2
    : descartado
      ? XCircle
      : enRevision
        ? AlertTriangle
        : Clock3;

  return (
    <section
      style={{
        backgroundColor: fondo,
        border: `1px solid ${borde}`,
        borderRadius: '10px',
        padding: '14px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
        <Icono size={19} style={{ color, flexShrink: 0, marginTop: '1px' }} />
        <div style={{ minWidth: 0 }}>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color }}>
            {confirmado
              ? 'Confirmado por el mecánico'
              : descartado
                ? 'Descartado por el mecánico'
                : enRevision
                  ? 'En revisión técnica'
                  : 'Pendiente de confirmación física'}
          </h4>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            {confirmado || descartado
              ? diagnostico.notas_mecanico || 'El mecánico registró la validación mediante WhatsApp.'
              : 'El administrador supervisa este resultado. La confirmación debe enviarla el mecánico desde WhatsApp con CONFIRMAR o DESCARTAR.'}
          </p>
          {diagnostico.fecha_confirmacion && (
            <span style={{ display: 'block', marginTop: '5px', fontSize: '11px', color: 'var(--text-muted)' }}>
              Responsable: {diagnostico.mecanico_nombre} · Registrado: {diagnostico.fecha_confirmacion}
            </span>
          )}
        </div>
      </div>
    </section>
  );
};
