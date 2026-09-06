import React from 'react';
import { ConfirmModal } from '../../../common/ConfirmModal';
import { Input } from '../../../common/Input';
import type { Mecanico, MecanicoRol } from '../../../../types';

interface EquipoTallerConfirmModalsProps {
  confirmRevocarModal: Mecanico | null;
  procesandoRevocacion: boolean;
  onConfirmRevocacion: () => Promise<void>;
  onCloseRevocacion: () => void;

  confirmActivarModal: { mecanico: Mecanico; estaActivando: boolean } | null;
  procesandoActivar: boolean;
  onConfirmActivar: () => Promise<void>;
  onCloseActivar: () => void;

  confirmBloquearModal: { mecanico: Mecanico; estaBloqueando: boolean } | null;
  procesandoBloquear: boolean;
  onConfirmBloquear: () => Promise<void>;
  onCloseBloquear: () => void;

  confirmRolModal: { mecanico: Mecanico; nuevoRol: MecanicoRol } | null;
  passwordNuevoAdmin: string;
  onPasswordNuevoAdminChange: (v: string) => void;
  procesandoRol: boolean;
  onConfirmRol: (id: string, rol: MecanicoRol) => Promise<void>;
  onCloseRol: () => void;
}

export const EquipoTallerConfirmModals: React.FC<EquipoTallerConfirmModalsProps> = ({
  confirmRevocarModal,
  procesandoRevocacion,
  onConfirmRevocacion,
  onCloseRevocacion,
  confirmActivarModal,
  procesandoActivar,
  onConfirmActivar,
  onCloseActivar,
  confirmBloquearModal,
  procesandoBloquear,
  onConfirmBloquear,
  onCloseBloquear,
  confirmRolModal,
  passwordNuevoAdmin,
  onPasswordNuevoAdminChange,
  procesandoRol,
  onConfirmRol,
  onCloseRol,
}) => {
  return (
    <>
      {/* 1. Modal Confirmar Revocación */}
      <ConfirmModal
        isOpen={!!confirmRevocarModal}
        title="Revocar Acceso Técnico"
        message={`¿Está seguro de que desea revocar el acceso a "${confirmRevocarModal?.nombres}"? El usuario no podrá interactuar con el chatbot de diagnóstico.`}
        confirmText="Revocar Acceso"
        cancelText="Cancelar"
        variant="danger"
        cargando={procesandoRevocacion}
        onConfirm={onConfirmRevocacion}
        onClose={onCloseRevocacion}
      />

      {/* 2. Modal Confirmar Activar / Desactivar */}
      <ConfirmModal
        isOpen={!!confirmActivarModal}
        title={confirmActivarModal?.estaActivando ? 'Habilitar Personal' : 'Desactivar Personal'}
        message={
          confirmActivarModal?.estaActivando
            ? `¿Desea habilitar la cuenta de "${confirmActivarModal?.mecanico.nombres}"? Podrá volver a enviar consultas por WhatsApp.`
            : `¿Desea suspender temporalmente a "${confirmActivarModal?.mecanico.nombres}"? Sus consultas quedarán pausadas.`
        }
        confirmText={confirmActivarModal?.estaActivando ? 'Habilitar Cuenta' : 'Suspender Cuenta'}
        cancelText="Cancelar"
        variant={confirmActivarModal?.estaActivando ? 'primary' : 'warning'}
        cargando={procesandoActivar}
        onConfirm={onConfirmActivar}
        onClose={onCloseActivar}
      />

      {/* 3. Modal Confirmar Bloquear / Desbloquear */}
      <ConfirmModal
        isOpen={!!confirmBloquearModal}
        title={confirmBloquearModal?.estaBloqueando ? 'Bloquear Usuario por Seguridad' : 'Desbloquear Usuario'}
        message={
          confirmBloquearModal?.estaBloqueando
            ? `¿Confirmar el bloqueo de seguridad para "${confirmBloquearModal?.mecanico.nombres}"? El sistema denegará todas las peticiones entrantes.`
            : `¿Desea desbloquear la cuenta de "${confirmBloquearModal?.mecanico.nombres}"?`
        }
        confirmText={confirmBloquearModal?.estaBloqueando ? 'Bloquear Usuario' : 'Desbloquear'}
        cancelText="Cancelar"
        variant={confirmBloquearModal?.estaBloqueando ? 'danger' : 'primary'}
        cargando={procesandoBloquear}
        onConfirm={onConfirmBloquear}
        onClose={onCloseBloquear}
      />

      {/* 4. Modal Confirmar Cambio de Rol */}
      {confirmRolModal && (
        <ConfirmModal
          isOpen={!!confirmRolModal}
          title="Cambiar Rol de Personal"
          message={
            confirmRolModal.nuevoRol === 'administrador'
              ? `Está por otorgar permisos de Administrador a "${confirmRolModal.mecanico.nombres}". Podrá gestionar usuarios, ver diagnósticos y configurar el sistema.`
              : `¿Desea cambiar el rol de "${confirmRolModal.mecanico.nombres}" a ${confirmRolModal.nuevoRol}?`
          }
          confirmText="Confirmar Cambio de Rol"
          cancelText="Cancelar"
          variant={confirmRolModal.nuevoRol === 'administrador' ? 'warning' : 'primary'}
          cargando={procesandoRol}
          onConfirm={() => onConfirmRol(confirmRolModal.mecanico.id, confirmRolModal.nuevoRol)}
          onClose={onCloseRol}
        >
          {confirmRolModal.nuevoRol === 'administrador' && (
            <div style={{ marginTop: '14px', textAlign: 'left' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                Asignar Contraseña del Panel de Administración *
              </label>
              <Input
                type="password"
                placeholder="Mínimo 12 caracteres (mayús, minús, números)..."
                value={passwordNuevoAdmin}
                onChange={(e) => onPasswordNuevoAdminChange(e.target.value)}
                required
              />
            </div>
          )}
        </ConfirmModal>
      )}
    </>
  );
};
