import React from 'react';
import { ConfirmModal } from '../../../common/ConfirmModal';
import type { Mecanico } from '../../../../types';

interface MecanicosModalsProps {
  confirmBloquearModal: { mecanico: Mecanico; estaBloqueando: boolean } | null;
  procesandoBloquear: boolean;
  onConfirmBloquear: () => Promise<void>;
  onCloseBloquear: () => void;

  confirmRevocarModal: Mecanico | null;
  procesandoRevocacion: boolean;
  onConfirmRevocar: () => Promise<void>;
  onCloseRevocar: () => void;
}

export const MecanicosModals: React.FC<MecanicosModalsProps> = ({
  confirmBloquearModal,
  procesandoBloquear,
  onConfirmBloquear,
  onCloseBloquear,
  confirmRevocarModal,
  procesandoRevocacion,
  onConfirmRevocar,
  onCloseRevocar,
}) => {
  return (
    <>
      {/* 1. Modal Confirmar Bloquear/Desbloquear */}
      <ConfirmModal
        isOpen={!!confirmBloquearModal}
        title={confirmBloquearModal?.estaBloqueando ? 'Bloquear Mecánico' : 'Desbloquear Mecánico'}
        message={
          confirmBloquearModal?.estaBloqueando
            ? `¿Está seguro de que desea bloquear a "${confirmBloquearModal?.mecanico.nombres}"? El mecánico no podrá solicitar diagnósticos ni interactuar con el chatbot de WhatsApp.`
            : `¿Desea desbloquear a "${confirmBloquearModal?.mecanico.nombres}"? Podrá volver a consultar diagnósticos inmediatamente.`
        }
        confirmText={confirmBloquearModal?.estaBloqueando ? 'Bloquear Mecánico' : 'Desbloquear'}
        cancelText="Cancelar"
        variant={confirmBloquearModal?.estaBloqueando ? 'danger' : 'primary'}
        cargando={procesandoBloquear}
        onConfirm={onConfirmBloquear}
        onClose={onCloseBloquear}
      />

      {/* 2. Modal Confirmar Revocar Acceso */}
      <ConfirmModal
        isOpen={!!confirmRevocarModal}
        title="Revocar Acceso de Mecánico"
        message={`¿Está seguro de que desea revocar el rol técnico a "${confirmRevocarModal?.nombres}"? Su número de WhatsApp dejará de tener privilegios de mecánico en el taller.`}
        confirmText="Revocar Acceso"
        cancelText="Cancelar"
        variant="danger"
        cargando={procesandoRevocacion}
        onConfirm={onConfirmRevocar}
        onClose={onCloseRevocar}
      />
    </>
  );
};
