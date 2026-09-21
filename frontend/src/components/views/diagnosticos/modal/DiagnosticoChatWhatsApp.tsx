import React, { useEffect, useRef } from 'react';
import { CheckCheck, MessageSquare, Bot } from 'lucide-react';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoChatWhatsAppProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoChatWhatsApp: React.FC<DiagnosticoChatWhatsAppProps> = ({
  diagnostico,
}) => {
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const formatearHora = (fechaIso?: string) => {
    if (!fechaIso) return 'Reciente';
    try {
      return new Date(fechaIso).toLocaleTimeString('es-PE', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return 'Reciente';
    }
  };

  const horaConsulta = formatearHora(diagnostico.fecha_hora);
  const horaConfirmacion = diagnostico.fecha_confirmacion
    ? formatearHora(diagnostico.fecha_confirmacion)
    : horaConsulta;

  const tieneValidacion =
    diagnostico.estado === 'confirmado' || diagnostico.estado === 'descartado';

  // Mantener scroll natural al final del chat para ver el diálogo completo
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [diagnostico]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#efeae2',
        borderRadius: '10px',
        border: '1px solid #d1d7db',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}
    >
      {/* Cabecera oficial WhatsApp Web */}
      <div
        style={{
          padding: '10px 14px',
          backgroundColor: '#075e54',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#25d366',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '13px',
            }}
          >
            <MessageSquare size={16} />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, lineHeight: 1.2 }}>
              {diagnostico.mecanico_nombre || 'Mecánico de Taller'}
            </div>
            <div style={{ fontSize: '11px', color: '#bbf7d0' }}>
              {diagnostico.cliente_telefono || '+51 9** *** ***'} · WhatsApp Webhook
            </div>
          </div>
        </div>

        <span
          style={{
            fontSize: '10.5px',
            backgroundColor: 'rgba(255, 255, 255, 0.18)',
            padding: '3px 8px',
            borderRadius: '12px',
            fontWeight: 600,
          }}
        >
          {diagnostico.modo_diagnostico === 'diagnostico_degradado_ml_rag'
            ? 'ML + RAG (Local)'
            : 'Completo (ML + RAG + LLM)'}
        </span>
      </div>

      {/* Área de Mensajes en Orden Cronológico (Flujo Conversacional Real) */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          backgroundImage: 'radial-gradient(#d1d7db 1px, transparent 1px)',
          backgroundSize: '16px 16px',
        }}
      >
        {/* Indicador de Fecha */}
        <div style={{ alignSelf: 'center', margin: '2px 0 6px' }}>
          <span
            style={{
              fontSize: '10.5px',
              backgroundColor: '#ffffff',
              color: '#54656f',
              padding: '3px 10px',
              borderRadius: '6px',
              boxShadow: '0 1px 1px rgba(0,0,0,0.08)',
              fontWeight: 600,
            }}
          >
            {diagnostico.fecha_hora ? diagnostico.fecha_hora.split(' ')[0] : 'Hoy'}
          </span>
        </div>

        {/* ================= TURNO 1: MENSAJE DEL MECÁNICO (PREGUNTA / SÍNTOMA) ================= */}
        <div
          style={{
            alignSelf: 'flex-start',
            maxWidth: '92%',
            backgroundColor: '#ffffff',
            padding: '10px 12px',
            borderRadius: '0 10px 10px 10px',
            boxShadow: '0 1px 2px rgba(0,0,0,0.12)',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#128c7e' }}>
              {diagnostico.mecanico_nombre || 'Mecánico'}
            </span>
            <span style={{ fontSize: '9.5px', color: '#64748b', backgroundColor: '#f1f5f9', padding: '1px 5px', borderRadius: '4px' }}>
              Turno 1 · Consulta
            </span>
          </div>

          <div
            style={{
              fontSize: '12px',
              color: '#111b21',
              lineHeight: 1.45,
              whiteSpace: 'pre-wrap',
              maxHeight: '160px',
              overflowY: 'auto',
              paddingRight: '2px',
            }}
          >
            "{diagnostico.sintoma_original}"
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', fontSize: '9.5px', color: '#667781', marginTop: '2px' }}>
            {horaConsulta}
          </div>
        </div>

        {/* ================= TURNO 2: RESPUESTA DEVUELTA POR CARBOT IA ================= */}
        <div
          style={{
            alignSelf: 'flex-end',
            maxWidth: '94%',
            backgroundColor: '#d9fdd3',
            padding: '10px 12px',
            borderRadius: '10px 0 10px 10px',
            boxShadow: '0 1px 2px rgba(0,0,0,0.12)',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            border: '1px solid #bbf7d0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Bot size={14} style={{ color: '#047857' }} />
              <span style={{ fontSize: '11px', fontWeight: 800, color: '#065f46' }}>
                CarBot IA · Diagnóstico
              </span>
            </div>
            <span
              style={{
                fontSize: '9.5px',
                fontWeight: 800,
                color: '#047857',
                backgroundColor: '#ffffff',
                padding: '1px 6px',
                borderRadius: '4px',
                border: '1px solid #86efac',
              }}
            >
              {diagnostico.confianza}% Certeza
            </span>
          </div>

          {/* Falla Principal */}
          <div
            style={{
              backgroundColor: '#ffffff',
              padding: '6px 8px',
              borderRadius: '6px',
              borderLeft: '3px solid #059669',
            }}
          >
            <div style={{ fontSize: '10px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
              Falla diagnosticada:
            </div>
            <div style={{ fontSize: '12.5px', fontWeight: 800, color: '#0f172a', marginTop: '1px' }}>
              {diagnostico.falla_predicha}
            </div>
          </div>

          {/* Procedimiento o Síntesis devuelta */}
          <div
            style={{
              fontSize: '11.5px',
              color: '#1e293b',
              lineHeight: 1.4,
              maxHeight: '140px',
              overflowY: 'auto',
              paddingRight: '2px',
            }}
          >
            {diagnostico.sintesis_llm ? (
              <div style={{ whiteSpace: 'pre-wrap' }}>{diagnostico.sintesis_llm}</div>
            ) : (
              <div>
                <strong style={{ color: '#065f46' }}>Procedimiento de taller recomendado:</strong>
                <div style={{ whiteSpace: 'pre-wrap', color: '#334155', marginTop: '2px' }}>
                  {diagnostico.procedimiento_rag}
                </div>
              </div>
            )}
          </div>

          {/* Comando para el mecánico */}
          <div
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.75)',
              padding: '5px 8px',
              borderRadius: '5px',
              fontSize: '10.5px',
              color: '#065f46',
            }}
          >
            👉 Responde <strong>CONFIRMAR</strong> o <strong>DESCARTAR [motivo]</strong> tras la inspección física.
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', fontSize: '9.5px', color: '#667781' }}>
            <span>{horaConsulta}</span>
            <CheckCheck size={13} style={{ color: '#53bdeb' }} />
          </div>
        </div>

        {/* ================= TURNO 3: RESPUESTA DE VALIDACIÓN DEL MECÁNICO (SI YA OCURRIÓ) ================= */}
        {tieneValidacion && (
          <div
            style={{
              alignSelf: 'flex-start',
              maxWidth: '92%',
              backgroundColor: '#ffffff',
              padding: '10px 12px',
              borderRadius: '0 10px 10px 10px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.12)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              borderLeft: `4px solid ${diagnostico.estado === 'confirmado' ? '#16a34a' : '#dc2626'}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#128c7e' }}>
                {diagnostico.mecanico_nombre || 'Mecánico'}
              </span>
              <span
                style={{
                  fontSize: '9.5px',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  backgroundColor: diagnostico.estado === 'confirmado' ? '#dcfce7' : '#fee2e2',
                  color: diagnostico.estado === 'confirmado' ? '#15803d' : '#b91c1c',
                }}
              >
                Turno 3 · {diagnostico.estado.toUpperCase()}
              </span>
            </div>

            <div style={{ fontSize: '12px', color: '#1e293b', lineHeight: 1.4 }}>
              <strong>{diagnostico.estado === 'confirmado' ? 'CONFIRMAR' : 'DESCARTAR'}:</strong>{' '}
              {diagnostico.notas_mecanico ||
                (diagnostico.estado === 'confirmado'
                  ? 'Falla confirmada físicamente tras inspección en taller.'
                  : 'Falla descartada tras inspección en taller.')}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', fontSize: '9.5px', color: '#667781', marginTop: '2px' }}>
              {horaConfirmacion}
            </div>
          </div>
        )}

        {/* ================= TURNO 4: CONFIRMACIÓN DE CARBOT (CIERRE DEL CASO) ================= */}
        {tieneValidacion && (
          <div
            style={{
              alignSelf: 'flex-end',
              maxWidth: '92%',
              backgroundColor: '#d9fdd3',
              padding: '8px 12px',
              borderRadius: '10px 0 10px 10px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.12)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              border: '1px solid #bbf7d0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Bot size={13} style={{ color: '#047857' }} />
              <span style={{ fontSize: '10.5px', fontWeight: 800, color: '#065f46' }}>
                CarBot IA · Cierre de Caso
              </span>
            </div>

            <div style={{ fontSize: '11.5px', color: '#1e293b', lineHeight: 1.35 }}>
              ✅ Validación registrada con éxito en el sistema como <strong>{diagnostico.estado.toUpperCase()}</strong>. Se actualizó el historial técnico del vehículo y la matriz de contrastación para las fichas de taller.
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px', fontSize: '9.5px', color: '#667781' }}>
              <span>{horaConfirmacion}</span>
              <CheckCheck size={13} style={{ color: '#53bdeb' }} />
            </div>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>
    </div>
  );
};
