import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Bot, CheckCheck, MessageSquare, RefreshCw, User } from 'lucide-react';
import type { Diagnostico } from '../../../../types';
import type { MensajeConversacion } from '../../../../types/domain';
import { apiService } from '../../../../services/api';

interface DiagnosticoChatWhatsAppProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoChatWhatsApp: React.FC<DiagnosticoChatWhatsAppProps> = ({
  diagnostico,
}) => {
  const [mensajes, setMensajes] = useState<MensajeConversacion[]>([]);
  const [cargando, setCargando] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const cargarConversacion = useCallback(async () => {
    if (!diagnostico.id) return;
    setCargando(true);
    setError(null);
    try {
      const data = await apiService.getConversacionDiagnostico(diagnostico.id);
      setMensajes(data);
    } catch {
      setError('No se pudo cargar el historial de mensajes de la conversación.');
    } finally {
      setCargando(false);
    }
  }, [diagnostico.id]);

  useEffect(() => {
    void cargarConversacion();
  }, [cargarConversacion]);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [mensajes]);

  const formatearHora = (fechaIso?: string) => {
    if (!fechaIso) return '';
    try {
      return new Date(fechaIso).toLocaleTimeString('es-PE', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return '';
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: '380px',
        maxHeight: '520px',
        backgroundColor: '#efeae2',
        borderRadius: '10px',
        border: '1px solid #d1d7db',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}
    >
      {/* Cabecera estilo WhatsApp */}
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
            }}
          >
            <MessageSquare size={16} />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, lineHeight: 1.2 }}>
              {diagnostico.mecanico_nombre || diagnostico.cliente_nombre || 'Mecánico de Taller'}
            </div>
            <div style={{ fontSize: '11px', color: '#bbf7d0' }}>
              {diagnostico.cliente_telefono || 'WhatsApp'} · Conversación Real
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={cargarConversacion}
          title="Actualizar mensajes"
          style={{
            background: 'transparent',
            border: 'none',
            color: '#ffffff',
            cursor: 'pointer',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <RefreshCw size={14} className={cargando ? 'spin' : ''} />
        </button>
      </div>

      {/* Cuerpo del Chat */}
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
        {cargando && (
          <div style={{ textAlign: 'center', padding: '24px', color: '#64748b', fontSize: '12px' }}>
            Cargando trazabilidad conversacional...
          </div>
        )}

        {error && (
          <div
            style={{
              backgroundColor: '#fee2e2',
              color: '#991b1b',
              padding: '10px 12px',
              borderRadius: '6px',
              fontSize: '11.5px',
              textAlign: 'center',
            }}
          >
            {error}
            <div style={{ marginTop: '6px' }}>
              <button
                type="button"
                onClick={cargarConversacion}
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  color: '#991b1b',
                  textDecoration: 'underline',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                Reintentar
              </button>
            </div>
          </div>
        )}

        {!cargando && !error && mensajes.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div
              style={{
                alignSelf: 'center',
                backgroundColor: '#ffffff',
                color: '#54656f',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '10.5px',
                boxShadow: '0 1px 1px rgba(0,0,0,0.06)',
              }}
            >
              Auditoría del registro
            </div>

            {/* Mensaje original del usuario */}
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '90%',
                backgroundColor: '#ffffff',
                padding: '8px 12px',
                borderRadius: '0 10px 10px 10px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.12)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '3px' }}>
                <User size={12} style={{ color: '#128c7e' }} />
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#128c7e' }}>
                  {diagnostico.mecanico_nombre || 'Mecánico'}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#111b21', whiteSpace: 'pre-wrap' }}>
                {diagnostico.sintoma_original}
              </div>
              <div style={{ fontSize: '9.5px', color: '#667781', textAlign: 'right', marginTop: '3px' }}>
                {formatearHora(diagnostico.fecha_hora)}
              </div>
            </div>

            {/* Respuesta emitida por CarBot */}
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '90%',
                backgroundColor: '#dcf8c6',
                padding: '8px 12px',
                borderRadius: '10px 0 10px 10px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.12)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '3px' }}>
                <Bot size={13} style={{ color: '#075e54' }} />
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#075e54' }}>
                  CarBot IA
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#111b21', whiteSpace: 'pre-wrap' }}>
                {diagnostico.sintesis_llm || diagnostico.procedimiento_rag || `Diagnóstico: ${diagnostico.falla_predicha} (${diagnostico.confianza}%)`}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '3px', marginTop: '3px' }}>
                <span style={{ fontSize: '9.5px', color: '#667781' }}>{formatearHora(diagnostico.fecha_hora)}</span>
                <CheckCheck size={12} style={{ color: '#34b7f1' }} />
              </div>
            </div>
          </div>
        )}

        {!cargando && !error && mensajes.map((msg) => {
          const esBot = msg.direccion === 'salida';
          return (
            <div
              key={msg.id}
              style={{
                alignSelf: esBot ? 'flex-end' : 'flex-start',
                maxWidth: '90%',
                backgroundColor: esBot ? '#dcf8c6' : '#ffffff',
                padding: '8px 12px',
                borderRadius: esBot ? '10px 0 10px 10px' : '0 10px 10px 10px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.12)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '3px' }}>
                {esBot ? (
                  <Bot size={13} style={{ color: '#075e54' }} />
                ) : (
                  <User size={12} style={{ color: '#128c7e' }} />
                )}
                <span style={{ fontSize: '11px', fontWeight: 700, color: esBot ? '#075e54' : '#128c7e' }}>
                  {esBot ? 'CarBot IA' : (diagnostico.mecanico_nombre || 'Mecánico')}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#111b21', whiteSpace: 'pre-wrap', lineHeight: 1.4 }}>
                {msg.texto || ''}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '3px', marginTop: '3px' }}>
                <span style={{ fontSize: '9.5px', color: '#667781' }}>
                  {formatearHora(msg.fecha_hora)}
                </span>
                {esBot && <CheckCheck size={12} style={{ color: '#34b7f1' }} />}
              </div>
            </div>
          );
        })}

        <div ref={chatBottomRef} />
      </div>
    </div>
  );
};
