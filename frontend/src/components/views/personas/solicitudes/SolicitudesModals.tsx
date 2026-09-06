import React from 'react';
import { Sparkles, AlertTriangle } from 'lucide-react';
import { Modal } from '../../../common/Modal';
import { Button } from '../../../common/Button';
import type { SolicitudAcceso } from '../../../../types';

interface SolicitudesModalsProps {
  modalAprobado: { abierto: boolean; nombreUsuario: string; telefono: string } | null;
  onCloseAprobado: () => void;
  modalRechazo: { abierto: boolean; solicitud: SolicitudAcceso | null } | null;
  onCloseRechazo: () => void;
  motivoRechazo: string;
  onMotivoRechazoChange: (v: string) => void;
  rechazando: boolean;
  errorRechazo: string | null;
  onConfirmRechazo: () => Promise<void>;
}

export const SolicitudesModals: React.FC<SolicitudesModalsProps> = ({
  modalAprobado,
  onCloseAprobado,
  modalRechazo,
  onCloseRechazo,
  motivoRechazo,
  onMotivoRechazoChange,
  rechazando,
  errorRechazo,
  onConfirmRechazo,
}) => {
  return (
    <>
      {/* 1. Modal Confirmación Aprobado */}
      {modalAprobado && (
        <Modal
          isOpen={modalAprobado.abierto}
          onClose={onCloseAprobado}
          title="Acceso Técnico Aprobado"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'center', padding: '12px 0' }}>
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                backgroundColor: 'rgba(16, 185, 129, 0.12)',
                color: '#10b981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto',
              }}
            >
              <Sparkles size={28} />
            </div>

            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)', margin: '0 0 6px 0' }}>
                ¡Personal Técnico Vinculado!
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                Se ha otorgado acceso a <strong>{modalAprobado.nombreUsuario}</strong> ({modalAprobado.telefono}).
                El usuario ya puede realizar consultas diagnósticas directamente por WhatsApp.
              </p>
            </div>

            <div style={{ marginTop: '8px' }}>
              <Button variant="primary" onClick={onCloseAprobado} style={{ width: '100%' }}>
                Entendido
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* 2. Modal Rechazar Solicitud */}
      {modalRechazo && (
        <Modal
          isOpen={modalRechazo.abierto}
          onClose={onCloseRechazo}
          title="Rechazar Solicitud de Acceso"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Indique el motivo por el cual se deniega el acceso a{' '}
              <strong>{modalRechazo.solicitud?.usuario_nombre}</strong>. Este motivo quedará registrado en la auditoría.
            </p>

            {errorRechazo && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 14px',
                  backgroundColor: '#fee2e2',
                  border: '1px solid #fca5a5',
                  borderRadius: 'var(--radius-sm)',
                  color: '#991b1b',
                  fontSize: '12px',
                }}
              >
                <AlertTriangle size={14} style={{ flexShrink: 0 }} />
                <span>{errorRechazo}</span>
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                Motivo del Rechazo *
              </label>
              <textarea
                value={motivoRechazo}
                onChange={(e) => onMotivoRechazoChange(e.target.value)}
                placeholder="Ej. No pertenece al equipo técnico del taller registrado..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  resize: 'vertical',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
              <Button variant="secondary" onClick={onCloseRechazo} disabled={rechazando}>
                Cancelar
              </Button>
              <Button variant="danger" onClick={onConfirmRechazo} disabled={rechazando}>
                {rechazando ? 'Procesando...' : 'Confirmar Rechazo'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};
