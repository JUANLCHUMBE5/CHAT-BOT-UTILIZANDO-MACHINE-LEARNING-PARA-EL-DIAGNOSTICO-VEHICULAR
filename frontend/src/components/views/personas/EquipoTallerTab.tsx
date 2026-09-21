import React from 'react';
import { PlusCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import type { Mecanico, UsuarioSesion } from '../../../types';
import { Button } from '../../common/Button';
import { useEquipoTallerActions } from '../../../hooks/useEquipoTallerActions';
import {
  EquipoTallerTable,
  EquipoTallerCreateModal,
  EquipoTallerEditModal,
  EquipoTallerConfirmModals,
} from './equipo';

export interface EquipoTallerTabProps {
  mecanicos: Mecanico[];
  cargando: boolean;
  currentUser: UsuarioSesion | null;
  onRecargar: () => void;
  onActualizarPerfilSesion?: (actualizado: Partial<UsuarioSesion>) => void;
}

export const EquipoTallerTab: React.FC<EquipoTallerTabProps> = ({
  mecanicos,
  cargando,
  currentUser,
  onRecargar,
  onActualizarPerfilSesion,
}) => {
  const actions = useEquipoTallerActions({
    mecanicos,
    currentUser,
    onRecargar,
    onActualizarPerfilSesion,
  });

  const esAdmin = currentUser?.rol === 'administrador' || currentUser?.rol === 'admin';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Toast de Éxito */}
      {actions.notificacionExito && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            backgroundColor: '#ecfdf5',
            color: '#065f46',
            border: '1px solid #a7f3d0',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={16} style={{ color: '#059669' }} />
            <span>{actions.notificacionExito}</span>
          </div>
          <button
            type="button"
            onClick={() => actions.setNotificacionExito(null)}
            style={{ background: 'none', border: 'none', color: '#065f46', cursor: 'pointer', fontSize: '13px' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Toast de Error */}
      {actions.notificacionError && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            backgroundColor: '#fee2e2',
            color: '#991b1b',
            border: '1px solid #fecaca',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} style={{ color: '#dc2626' }} />
            <span>{actions.notificacionError}</span>
          </div>
          <button
            type="button"
            onClick={() => actions.setNotificacionError(null)}
            style={{ background: 'none', border: 'none', color: '#991b1b', cursor: 'pointer', fontSize: '13px' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Barra de Acciones y Título */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Equipo Técnico del Taller
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
            Personal autorizado con roles, permisos de diagnóstico y credenciales de acceso.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => actions.setModalNuevoAbierto(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <PlusCircle size={15} />
          <span>Registrar Personal</span>
        </Button>
      </div>

      {/* Tabla del Personal Técnico */}
      <EquipoTallerTable
        mecanicos={mecanicos}
        cargando={cargando}
        evaluateRowGuards={actions.evaluateRowGuards}
        onAbrirEdicion={actions.handleAbrirEdicion}
        onConfirmActivar={(data) => actions.setConfirmActivarModal(data)}
        onConfirmBloquear={(data) => actions.setConfirmBloquearModal(data)}
        onSeleccionarRol={actions.handleSeleccionarRol}
        onConfirmRevocar={(m) => actions.setConfirmRevocarModal(m)}
      />

      {/* Modal Registrar Nuevo */}
      <EquipoTallerCreateModal
        isOpen={actions.modalNuevoAbierto}
        onClose={() => actions.setModalNuevoAbierto(false)}
        onSubmit={actions.handleCrearNuevoMecanico}
        nombre={actions.nuevoNombre}
        onNombreChange={actions.setNuevoNombre}
        username={actions.nuevoUsername}
        onUsernameChange={actions.setNuevoUsername}
        telefono={actions.nuevoTelefono}
        onTelefonoChange={actions.setNuevoTelefono}
        password={actions.nuevoPassword}
        onPasswordChange={actions.setNuevoPassword}
        rol={actions.nuevoRol}
        onRolChange={actions.setNuevoRol}
        guardando={actions.guardandoNuevo}
        error={actions.errorNuevo}
        esAdmin={esAdmin}
      />

      {/* Modal Editar */}
      <EquipoTallerEditModal
        mecanico={actions.mecanicoAEditar}
        onClose={() => actions.setMecanicoAEditar(null)}
        onSubmit={actions.handleGuardarEdicion}
        nombres={actions.editNombres}
        onNombresChange={actions.setEditNombres}
        username={actions.editUsername}
        onUsernameChange={actions.setEditUsername}
        telefono={actions.editTelefono}
        onTelefonoChange={actions.setEditTelefono}
        password={actions.editPassword}
        onPasswordChange={actions.setEditPassword}
        deseaCambiarPassword={actions.deseaCambiarPassword}
        onDeseaCambiarPasswordChange={actions.setDeseaCambiarPassword}
        guardando={actions.guardandoEdicion}
        error={actions.errorEdicion}
      />

      {/* Modales de Confirmación */}
      <EquipoTallerConfirmModals
        confirmRevocarModal={actions.confirmRevocarModal}
        procesandoRevocacion={actions.procesandoRevocacion}
        onConfirmRevocacion={actions.handleConfirmarRevocacion}
        onCloseRevocacion={() => actions.setConfirmRevocarModal(null)}
        confirmActivarModal={actions.confirmActivarModal}
        procesandoActivar={actions.procesandoActivar}
        onConfirmActivar={actions.ejecutarToggleActivar}
        onCloseActivar={() => actions.setConfirmActivarModal(null)}
        confirmBloquearModal={actions.confirmBloquearModal}
        procesandoBloquear={actions.procesandoBloquear}
        onConfirmBloquear={actions.ejecutarToggleBloquear}
        onCloseBloquear={() => actions.setConfirmBloquearModal(null)}
        confirmRolModal={actions.confirmRolModal}
        passwordNuevoAdmin={actions.passwordNuevoAdmin}
        onPasswordNuevoAdminChange={actions.setPasswordNuevoAdmin}
        procesandoRol={actions.procesandoRol}
        onConfirmRol={actions.ejecutarCambioRol}
        onCloseRol={() => actions.setConfirmRolModal(null)}
      />
    </div>
  );
};
