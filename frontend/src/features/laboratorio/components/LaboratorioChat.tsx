import React, { useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';

export interface ChatEntry {
  emisor: 'usuario' | 'carbot';
  texto: string;
  tiempoMs?: number;
  timestamp: string;
}

interface LaboratorioChatProps {
  sessionId: string;
  historial: ChatEntry[];
  inputMensaje: string;
  cargando: boolean;
  onInputChange: (texto: string) => void;
  onEnviar: (texto: string) => void;
}

export const LaboratorioChat: React.FC<LaboratorioChatProps> = ({
  sessionId,
  historial,
  inputMensaje,
  cargando,
  onInputChange,
  onEnviar,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [historial]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--surface-card, #ffffff)',
        borderRadius: '12px',
        border: '1px solid var(--border-color, #e5e7eb)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-color, #e5e7eb)',
          background: '#f9fafb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '13px', fontWeight: 600, color: '#374151' }}>
          Canal de Conversación (Sesión: {sessionId})
        </span>
        <span style={{ fontSize: '11px', color: '#6b7280' }}>
          {historial.length} mensajes intercambiados
        </span>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          background: '#f3f4f6',
        }}
      >
        {historial.length === 0 ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#9ca3af',
              gap: '8px',
              textAlign: 'center',
              padding: '30px',
            }}
          >
            <Sparkles size={32} />
            <p style={{ margin: 0, fontSize: '14px', fontWeight: 500 }}>
              Laboratorio listo. Envía una consulta técnica o reproduce los casos auditados.
            </p>
            <p style={{ margin: 0, fontSize: '12px' }}>
              Ejemplo: "Toyota Yaris 2020, placa ABC-123. Chirrido al frenar y pedal vibra."
            </p>
          </div>
        ) : (
          historial.map((entry, idx) => (
            <div
              key={idx}
              style={{
                alignSelf: entry.emisor === 'usuario' ? 'flex-end' : 'flex-start',
                maxWidth: '85%',
                background: entry.emisor === 'usuario' ? '#2563eb' : '#ffffff',
                color: entry.emisor === 'usuario' ? '#ffffff' : '#1f2937',
                padding: '10px 14px',
                borderRadius: entry.emisor === 'usuario' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.06)',
                fontSize: '13.5px',
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
              }}
            >
              <div>{entry.texto}</div>
              <div
                style={{
                  fontSize: '10px',
                  color: entry.emisor === 'usuario' ? 'rgba(255,255,255,0.7)' : '#9ca3af',
                  marginTop: '4px',
                  textAlign: 'right',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: '8px',
                }}
              >
                {entry.tiempoMs && <span>⚡ {entry.tiempoMs} ms</span>}
                <span>{entry.timestamp}</span>
              </div>
            </div>
          ))
        )}
        <div ref={scrollRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onEnviar(inputMensaje);
        }}
        style={{
          padding: '12px',
          borderTop: '1px solid var(--border-color, #e5e7eb)',
          display: 'flex',
          gap: '8px',
          background: '#ffffff',
        }}
      >
        <input
          type="text"
          value={inputMensaje}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder="Escribe una consulta técnica vehicular..."
          disabled={cargando}
          style={{
            flex: 1,
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid #d1d5db',
            fontSize: '13px',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={cargando || !inputMensaje.trim()}
          style={{
            padding: '10px 16px',
            borderRadius: '8px',
            background: '#2563eb',
            color: '#ffffff',
            border: 'none',
            cursor: cargando || !inputMensaje.trim() ? 'not-allowed' : 'pointer',
            opacity: cargando || !inputMensaje.trim() ? 0.6 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontWeight: 600,
          }}
        >
          <Send size={15} />
          Enviar
        </button>
      </form>
    </div>
  );
};
