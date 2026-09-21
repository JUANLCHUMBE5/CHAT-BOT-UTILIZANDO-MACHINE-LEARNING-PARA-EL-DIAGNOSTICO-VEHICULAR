import React, { useState } from 'react';
import type { Mecanico, MecanicoRol, MecanicoUpdateDTO, UsuarioSesion } from '../types';
import { apiService } from '../services/api';
import { getErrorMessage } from '../utils/errors';

export interface RowGuards {
  isSelf: boolean;
  isAdmin: boolean;
  isLastActiveAdmin: boolean;
  restrictedByHierarchy: boolean;
  canEdit: boolean;
  canToggleActive: boolean;
  canToggleBlock: boolean;
  canChangeRole: (nuevoRolTarget: MecanicoRol) => boolean;
  canRevoke: boolean;
  editTooltip: string;
  activeTooltip: string;
  blockTooltip: string;
  revokeTooltip: string;
}

export interface UseEquipoTallerActionsProps {
  mecanicos: Mecanico[];
  currentUser: UsuarioSesion | null;
  onRecargar: () => void;
  onActualizarPerfilSesion?: (actualizado: Partial<UsuarioSesion>) => void;
}

export const useEquipoTallerActions = ({
  mecanicos,
  currentUser,
  onRecargar,
  onActualizarPerfilSesion,
}: UseEquipoTallerActionsProps) => {
  // Feedback notifications
  const [notificacionError, setNotificacionError] = useState<string | null>(null);
  const [notificacionExito, setNotificacionExito] = useState<string | null>(null);

  // Modal de registro manual de nuevo personal
  const [modalNuevoAbierto, setModalNuevoAbierto] = useState(false);
  const [nuevoNombre, setNuevoNombre] = useState('');
  const [nuevoUsername, setNuevoUsername] = useState('');
  const [nuevoTelefono, setNuevoTelefono] = useState('');
  const [nuevoPassword, setNuevoPassword] = useState('');
  const [nuevoRol, setNuevoRol] = useState<MecanicoRol>('mecanico');
  const [guardandoNuevo, setGuardandoNuevo] = useState(false);
  const [errorNuevo, setErrorNuevo] = useState<string | null>(null);

  // Modal de edición de datos de personal
  const [mecanicoAEditar, setMecanicoAEditar] = useState<Mecanico | null>(null);
  const [editNombres, setEditNombres] = useState('');
  const [editUsername, setEditUsername] = useState('');
  const [editTelefono, setEditTelefono] = useState('');
  const [editPassword, setEditPassword] = useState('');
  const [deseaCambiarPassword, setDeseaCambiarPassword] = useState(false);
  const [guardandoEdicion, setGuardandoEdicion] = useState(false);
  const [errorEdicion, setErrorEdicion] = useState<string | null>(null);

  // Modales de confirmación para todas las acciones administrativas
  const [confirmRevocarModal, setConfirmRevocarModal] = useState<Mecanico | null>(null);
  const [procesandoRevocacion, setProcesandoRevocacion] = useState(false);

  const [confirmActivarModal, setConfirmActivarModal] = useState<{
    mecanico: Mecanico;
    estaActivando: boolean;
  } | null>(null);
  const [procesandoActivar, setProcesandoActivar] = useState(false);

  const [confirmBloquearModal, setConfirmBloquearModal] = useState<{
    mecanico: Mecanico;
    estaBloqueando: boolean;
  } | null>(null);
  const [procesandoBloquear, setProcesandoBloquear] = useState(false);

  const [confirmRolModal, setConfirmRolModal] = useState<{
    mecanico: Mecanico;
    nuevoRol: MecanicoRol;
  } | null>(null);
  const [passwordNuevoAdmin, setPasswordNuevoAdmin] = useState('');
  const [procesandoRol, setProcesandoRol] = useState(false);

  // Permissions helper
  const esAdmin = currentUser?.rol === 'administrador' || currentUser?.rol === 'admin';

  // Count active administrators in workshop
  const activeAdminCount = mecanicos.filter(
    (m) => (m.rol === 'administrador' || (m.rol as string) === 'admin') && m.activo && !m.bloqueado
  ).length;

  const evaluateRowGuards = (mecanico: Mecanico) => {
    const isSelf = currentUser
      ? Boolean(
          (currentUser.id && mecanico.id === currentUser.id) ||
          (currentUser.nombre && mecanico.nombres.toLowerCase() === currentUser.nombre.toLowerCase()) ||
          (currentUser.username && mecanico.nombres.toLowerCase() === currentUser.username.toLowerCase())
        )
      : false;

    const isMecanicoAdmin = mecanico.rol === 'administrador' || (mecanico.rol as string) === 'admin';
    const isLastActiveAdmin = isMecanicoAdmin && mecanico.activo && !mecanico.bloqueado && activeAdminCount <= 1;
    const restrictedByHierarchy = !esAdmin && isMecanicoAdmin;

    return {
      isSelf,
      isAdmin: isMecanicoAdmin,
      isLastActiveAdmin,
      restrictedByHierarchy,
      canEdit: !restrictedByHierarchy,
      canToggleActive: !isSelf && !isLastActiveAdmin && !restrictedByHierarchy,
      canToggleBlock: !isSelf && !isLastActiveAdmin && !restrictedByHierarchy,
      canChangeRole: (nuevoRolTarget: MecanicoRol) => {
        if (!esAdmin && nuevoRolTarget === 'administrador') return false;
        if (restrictedByHierarchy) return false;
        if (isSelf && isMecanicoAdmin && nuevoRolTarget !== 'administrador') return false;
        if (isLastActiveAdmin && nuevoRolTarget !== 'administrador') return false;
        return true;
      },
      canRevoke: !isSelf && !isMecanicoAdmin && !restrictedByHierarchy,
      editTooltip: restrictedByHierarchy
        ? 'Solo administradores pueden modificar cuentas de administrador'
        : '',
      activeTooltip: isSelf
        ? 'No puedes desactivar tu propia cuenta'
        : isLastActiveAdmin
        ? 'Único administrador activo del taller'
        : restrictedByHierarchy
        ? 'Solo administradores pueden modificar cuentas de administrador'
        : '',
      blockTooltip: isSelf
        ? 'No puedes bloquear tu propia cuenta'
        : isLastActiveAdmin
        ? 'Único administrador activo del taller'
        : restrictedByHierarchy
        ? 'Solo administradores pueden bloquear cuentas de administrador'
        : '',
      revokeTooltip: isSelf
        ? 'No puedes revocar tu propio acceso'
        : isMecanicoAdmin
        ? 'Un administrador no puede revocarse directamente. Asigne otro rol previamente.'
        : restrictedByHierarchy
        ? 'Solo administradores pueden gestionar permisos'
        : '',
    };
  };

  const ejecutarToggleActivar = async () => {
    if (!confirmActivarModal) return;
    setProcesandoActivar(true);
    setNotificacionError(null);
    try {
      await apiService.toggleActivarMecanico(confirmActivarModal.mecanico.id);
      setNotificacionExito(`Estado de ${confirmActivarModal.mecanico.nombres} actualizado correctamente.`);
      setConfirmActivarModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al cambiar estado de activación'));
    } finally {
      setProcesandoActivar(false);
    }
  };

  const ejecutarToggleBloquear = async () => {
    if (!confirmBloquearModal) return;
    setProcesandoBloquear(true);
    setNotificacionError(null);
    try {
      await apiService.toggleBloquearMecanico(confirmBloquearModal.mecanico.id);
      setNotificacionExito(`Estado de bloqueo de ${confirmBloquearModal.mecanico.nombres} modificado.`);
      setConfirmBloquearModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al cambiar estado de bloqueo'));
    } finally {
      setProcesandoBloquear(false);
    }
  };

  const handleSeleccionarRol = (m: Mecanico, targetRol: MecanicoRol) => {
    if (m.rol === targetRol) return;
    const guards = evaluateRowGuards(m);
    if (!guards.canChangeRole(targetRol)) {
      setNotificacionError(
        guards.isSelf
          ? 'No puedes reducir tu propio rol de administrador.'
          : guards.isLastActiveAdmin
          ? 'No se puede cambiar el rol del único administrador activo del taller.'
          : guards.restrictedByHierarchy
          ? 'Solo un administrador puede modificar o asignar privilegios de administrador.'
          : 'No tienes permisos para realizar este cambio de rol.'
      );
      return;
    }

    setPasswordNuevoAdmin('');
    setConfirmRolModal({ mecanico: m, nuevoRol: targetRol });
  };

  const ejecutarCambioRol = async (mecanicoId: string, nuevoRol: MecanicoRol) => {
    const passwordAdmin = passwordNuevoAdmin.trim();
    if (
      nuevoRol === 'administrador' &&
      (passwordAdmin.length < 12 ||
        !/[a-z]/.test(passwordAdmin) ||
        !/[A-Z]/.test(passwordAdmin) ||
        !/\d/.test(passwordAdmin))
    ) {
      setNotificacionError(
        'Para habilitar el panel al nuevo administrador, asigne una contraseña de 12 caracteres con mayúsculas, minúsculas y números.'
      );
      return;
    }
    setProcesandoRol(true);
    setNotificacionError(null);
    try {
      await apiService.cambiarRolMecanico(
        mecanicoId,
        nuevoRol,
        nuevoRol === 'administrador' ? passwordAdmin : undefined
      );
      setNotificacionExito(`Rol actualizado a ${nuevoRol} correctamente.`);
      setConfirmRolModal(null);
      setPasswordNuevoAdmin('');
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al cambiar rol del personal'));
    } finally {
      setProcesandoRol(false);
    }
  };

  const handleConfirmarRevocacion = async () => {
    if (!confirmRevocarModal) return;
    setProcesandoRevocacion(true);
    setNotificacionError(null);
    try {
      await apiService.revocarAccesoMecanico(confirmRevocarModal.id);
      setNotificacionExito(`Acceso técnico de ${confirmRevocarModal.nombres} revocado.`);
      setConfirmRevocarModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al revocar acceso técnico'));
    } finally {
      setProcesandoRevocacion(false);
    }
  };

  const handleCrearNuevoMecanico = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorNuevo(null);

    const nombreTrim = nuevoNombre.trim();
    const telTrim = nuevoTelefono.trim();
    const passTrim = nuevoPassword.trim();

    if (!nombreTrim || !telTrim) {
      setErrorNuevo('El nombre y el teléfono son obligatorios.');
      return;
    }

    if (
      nuevoRol === 'administrador' &&
      (passTrim.length < 12 ||
        !/[a-z]/.test(passTrim) ||
        !/[A-Z]/.test(passTrim) ||
        !/\d/.test(passTrim))
    ) {
      setErrorNuevo(
        'La cuenta administrativa requiere una contraseña de 12 caracteres con mayúsculas, minúsculas y números.'
      );
      return;
    }

    if (nuevoRol === 'administrador' && !esAdmin) {
      setErrorNuevo('Solo un administrador puede registrar usuarios con rol de administrador.');
      return;
    }

    setGuardandoNuevo(true);
    try {
      await apiService.registrarMecanico({
        nombres: nombreTrim,
        username: nuevoUsername.trim() ? nuevoUsername.trim().toLowerCase() : undefined,
        telefono_whatsapp: telTrim,
        password: nuevoRol === 'administrador' ? passTrim : undefined,
        rol: nuevoRol,
      });
      setModalNuevoAbierto(false);
      setNuevoNombre('');
      setNuevoUsername('');
      setNuevoTelefono('');
      setNuevoPassword('');
      setNuevoRol('mecanico');
      setNotificacionExito(`Personal ${nombreTrim} registrado exitosamente.`);
      onRecargar();
    } catch (error: unknown) {
      setErrorNuevo(getErrorMessage(error, 'Error al registrar nuevo personal'));
    } finally {
      setGuardandoNuevo(false);
    }
  };

  const handleAbrirEdicion = (m: Mecanico) => {
    const guards = evaluateRowGuards(m);
    if (!guards.canEdit) {
      setNotificacionError(
        guards.restrictedByHierarchy
          ? 'Solo un administrador puede editar perfiles con rol de administrador.'
          : 'No tienes permisos para editar este perfil.'
      );
      return;
    }
    setMecanicoAEditar(m);
    setEditNombres(m.nombres || '');
    setEditUsername(m.username || '');
    setEditTelefono(m.telefono || '');
    setEditPassword('');
    setDeseaCambiarPassword(false);
    setErrorEdicion(null);
  };

  const handleGuardarEdicion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mecanicoAEditar) return;
    setErrorEdicion(null);

    const nombresTrim = editNombres.trim();
    const telTrim = editTelefono.trim();
    const passTrim = editPassword.trim();

    if (!nombresTrim) {
      setErrorEdicion('El nombre completo es obligatorio.');
      return;
    }

    if (
      deseaCambiarPassword &&
      (mecanicoAEditar.rol === 'administrador' || (mecanicoAEditar.rol as string) === 'admin')
    ) {
      if (
        passTrim.length < 12 ||
        !/[a-z]/.test(passTrim) ||
        !/[A-Z]/.test(passTrim) ||
        !/\d/.test(passTrim)
      ) {
        setErrorEdicion(
          'La nueva contraseña debe tener mínimo 12 caracteres e incluir mayúsculas, minúsculas y números.'
        );
        return;
      }
    }

    setGuardandoEdicion(true);
    try {
      const payload: MecanicoUpdateDTO = {
        nombres: nombresTrim,
        username: editUsername.trim() ? editUsername.trim().toLowerCase() : undefined,
        telefono_whatsapp: telTrim || undefined,
        password: deseaCambiarPassword && passTrim ? passTrim : undefined,
      };

      const actualizado = await apiService.actualizarMecanico(mecanicoAEditar.id, payload);

      if (
        currentUser &&
        (currentUser.id === mecanicoAEditar.id ||
          currentUser.username === mecanicoAEditar.username)
      ) {
        if (onActualizarPerfilSesion) {
          onActualizarPerfilSesion({
            nombre: actualizado.nombres,
            username: actualizado.username || currentUser.username,
          });
        }
      }

      setMecanicoAEditar(null);
      setNotificacionExito(`Perfil de ${actualizado.nombres} actualizado correctamente.`);
      onRecargar();
    } catch (error: unknown) {
      setErrorEdicion(getErrorMessage(error, 'Error al actualizar el perfil'));
    } finally {
      setGuardandoEdicion(false);
    }
  };

  return {
    notificacionError,
    setNotificacionError,
    notificacionExito,
    setNotificacionExito,
    modalNuevoAbierto,
    setModalNuevoAbierto,
    nuevoNombre,
    setNuevoNombre,
    nuevoUsername,
    setNuevoUsername,
    nuevoTelefono,
    setNuevoTelefono,
    nuevoPassword,
    setNuevoPassword,
    nuevoRol,
    setNuevoRol,
    guardandoNuevo,
    errorNuevo,
    handleCrearNuevoMecanico,
    mecanicoAEditar,
    setMecanicoAEditar,
    editNombres,
    setEditNombres,
    editUsername,
    setEditUsername,
    editTelefono,
    setEditTelefono,
    editPassword,
    setEditPassword,
    deseaCambiarPassword,
    setDeseaCambiarPassword,
    guardandoEdicion,
    errorEdicion,
    handleAbrirEdicion,
    handleGuardarEdicion,
    confirmRevocarModal,
    setConfirmRevocarModal,
    procesandoRevocacion,
    handleConfirmarRevocacion,
    confirmActivarModal,
    setConfirmActivarModal,
    procesandoActivar,
    ejecutarToggleActivar,
    confirmBloquearModal,
    setConfirmBloquearModal,
    procesandoBloquear,
    ejecutarToggleBloquear,
    confirmRolModal,
    setConfirmRolModal,
    passwordNuevoAdmin,
    setPasswordNuevoAdmin,
    procesandoRol,
    handleSeleccionarRol,
    ejecutarCambioRol,
    evaluateRowGuards,
  };
};
