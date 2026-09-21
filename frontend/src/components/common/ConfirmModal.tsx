import React from 'react';
import { Modal } from './Modal';
import { AlertTriangle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';

export interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'primary' | 'success';
  cargando?: boolean;
  children?: React.ReactNode;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  variant = 'danger',
  cargando = false,
  children,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          icon: <ShieldAlert size={24} color="#ef4444" />,
          bgIcon: 'rgba(239, 68, 68, 0.1)',
          btnBg: '#ef4444',
          btnHoverBg: '#dc2626',
        };
      case 'warning':
        return {
          icon: <AlertTriangle size={24} color="#f59e0b" />,
          bgIcon: 'rgba(245, 158, 11, 0.1)',
          btnBg: '#f59e0b',
          btnHoverBg: '#d97706',
        };
      case 'success':
        return {
          icon: <CheckCircle2 size={24} color="#10b981" />,
          bgIcon: 'rgba(16, 185, 129, 0.1)',
          btnBg: '#10b981',
          btnHoverBg: '#059669',
        };
      default:
        return {
          icon: <Info size={24} color="#3b82f6" />,
          bgIcon: 'rgba(59, 130, 246, 0.1)',
          btnBg: '#3b82f6',
          btnHoverBg: '#2563eb',
        };
    }
  };

  const vStyles = getVariantStyles();

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} maxWidth="480px">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              backgroundColor: vStyles.bgIcon,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {vStyles.icon}
          </div>
          <div style={{ flex: 1, fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {message}
            {children}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
            marginTop: '8px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-color)',
          }}
        >
          <button
            type="button"
            onClick={onClose}
            disabled={cargando}
            style={{
              padding: '8px 16px',
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              cursor: cargando ? 'not-allowed' : 'pointer',
            }}
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={cargando}
            style={{
              padding: '8px 18px',
              backgroundColor: vStyles.btnBg,
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              fontWeight: 600,
              color: '#ffffff',
              cursor: cargando ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            {cargando ? 'Procesando...' : confirmText}
          </button>
        </div>
      </div>
    </Modal>
  );
};
