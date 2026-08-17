import React, { useState } from 'react';
import {
  ShieldAlert,
  Power,
  Lock,
  Unlock,
  PlusCircle,
  AlertTriangle,
  CheckCircle2,
  Pencil,
  Loader2
} from 'lucide-react';
import type { Mecanico, MecanicoRol, MecanicoUpdateDTO, UsuarioSesion } from '../../../types';
import { ConfirmModal } from '../../common/ConfirmModal';
import { Modal } from '../../common/Modal';
import { getErrorMessage } from '../../../utils/errors';
import { apiService } from '../../../services/api';

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
  // Feedback notifications (replaces native alert)
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

  const getRoleBadgeStyle = (rol: string) => {
    switch (rol) {
      case 'administrador':
      case 'admin':
        return { label: 'Administrador', bg: 'rgba(99, 102, 241, 0.15)', color: '#4338ca' };
      case 'jefe_taller':
      case 'supervisor':
        return { label: 'Jefe de Taller', bg: 'rgba(245, 158, 11, 0.15)', color: '#b45309' };
      default:
        return { label: 'Mecánico', bg: 'rgba(16, 185, 129, 0.15)', color: '#047857' };
    }
  };

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

    // Jefe de taller cannot modify administrators
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

  // Execution Handlers with Modal Confirmation
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
    if (nuevoRol === 'administrador' && (
      passwordAdmin.length < 12 ||
      !/[a-z]/.test(passwordAdmin) ||
      !/[A-Z]/.test(passwordAdmin) ||
      !/\d/.test(passwordAdmin)
    )) {
      setNotificacionError('Para habilitar el panel al nuevo administrador, asigne una contraseña de 12 caracteres con mayúsculas, minúsculas y números.');
      return;
    }
    setProcesandoRol(true);
    setNotificacionError(null);
    try {
      await apiService.cambiarRolMecanico(mecanicoId, nuevoRol, nuevoRol === 'administrador' ? passwordAdmin : undefined);
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
      await apiService.eliminarMecanico(confirmRevocarModal.id);
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

    // Solo el administrador usa credenciales del panel web.
    if (nuevoRol === 'administrador' && (
      passTrim.length < 12 ||
      !/[a-z]/.test(passTrim) ||
      !/[A-Z]/.test(passTrim) ||
      !/\d/.test(passTrim)
    )) {
      setErrorNuevo('La cuenta administrativa requiere una contraseña de 12 caracteres con mayúsculas, minúsculas y números.');
      return;
    }

    // Role guard: jefe de taller cannot create administrators
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
      setErrorNuevo(getErrorMessage(error, 'Error al registrar personal'));
    } finally {
      setGuardandoNuevo(false);
    }
  };

  const handleAbrirModalEditar = (m: Mecanico) => {
    setMecanicoAEditar(m);
    setEditNombres(m.nombres || '');
    setEditUsername(m.username || '');
    setEditTelefono('');
    setEditPassword('');
    setDeseaCambiarPassword(false);
    setErrorEdicion(null);
  };

  const handleGuardarEdicion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mecanicoAEditar) return;
    setErrorEdicion(null);

    const nombreTrim = editNombres.trim();
    if (!nombreTrim) {
      setErrorEdicion('El nombre completo no puede estar vacío.');
      return;
    }

    const usernameTrim = editUsername.trim().toLowerCase();

    const editandoAdmin = mecanicoAEditar.rol === 'administrador' || (mecanicoAEditar.rol as string) === 'admin';
    const passTrim = editPassword.trim();

    if (deseaCambiarPassword && editandoAdmin) {
      if (
        passTrim.length < 12 ||
        !/[a-z]/.test(passTrim) ||
        !/[A-Z]/.test(passTrim) ||
        !/\d/.test(passTrim)
      ) {
        setErrorEdicion('La nueva contraseña debe tener al menos 12 caracteres e incluir mayúsculas, minúsculas y números.');
        return;
      }
    }

    const telTrim = editTelefono.trim();
    const payload: MecanicoUpdateDTO = {
      nombres: nombreTrim,
      username: usernameTrim || undefined,
    };

    if (telTrim) {
      if (telTrim.includes('*')) {
        setErrorEdicion('Para actualizar el teléfono, ingrese el nuevo número completo (sin asteriscos).');
        return;
      }
      const digits = telTrim.replace(/\D/g, '');
      if (digits.length < 6) {
        setErrorEdicion('El número de teléfono WhatsApp debe contener al menos 6 dígitos válidos.');
        return;
      }
      payload.telefono_whatsapp = telTrim;
    }

    if (deseaCambiarPassword && editandoAdmin && passTrim.length > 0) {
      payload.password = passTrim;
    }

    setGuardandoEdicion(true);
    try {
      await apiService.actualizarMecanico(mecanicoAEditar.id, payload);
      setNotificacionExito(`Perfil de ${nombreTrim} actualizado exitosamente.`);

      const isCurrentUser = Boolean(
        (currentUser?.id && mecanicoAEditar.id === currentUser.id) ||
        (currentUser?.nombre && mecanicoAEditar.nombres.toLowerCase() === currentUser.nombre.toLowerCase()) ||
        (currentUser?.username && (mecanicoAEditar.username || mecanicoAEditar.nombres).toLowerCase() === currentUser.username.toLowerCase())
      );

      if (isCurrentUser && onActualizarPerfilSesion) {
        onActualizarPerfilSesion({
          nombre: nombreTrim,
          username: usernameTrim || currentUser?.username || nombreTrim,
        });
      }

      setMecanicoAEditar(null);
      setErrorEdicion(null);
      onRecargar();
    } catch (error: unknown) {
      setErrorEdicion(getErrorMessage(error, 'Error al actualizar el perfil del mecánico'));
    } finally {
      setGuardandoEdicion(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Action Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Personal Técnico y Administrativo
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Gestiona los roles, activación y accesos del equipo de trabajo.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setModalNuevoAbierto(true);
            setErrorNuevo(null);
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '9px 16px',
            backgroundColor: '#3b82f6',
            color: '#ffffff',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <PlusCircle size={16} />
          <span>Registrar Nuevo Personal</span>
        </button>
      </div>

      {/* In-app Notification Banners */}
      {notificacionError && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#b91c1c',
            fontSize: '13px',
          }}
        >
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <span style={{ flex: 1 }}>{notificacionError}</span>
          <button
            type="button"
            onClick={() => setNotificacionError(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b91c1c', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {notificacionExito && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#047857',
            fontSize: '13px',
          }}
        >
          <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
          <span style={{ flex: 1 }}>{notificacionExito}</span>
          <button
            type="button"
            onClick={() => setNotificacionExito(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#047857', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Staff List Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Nombre del Personal</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Teléfono</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Rol de Usuario</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Estado Cuenta</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Diagnósticos</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'right' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Cargando equipo del taller...
                </td>
              </tr>
            ) : mecanicos.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No hay personal técnico o administrativo registrado.
                </td>
              </tr>
            ) : (
              mecanicos.map((m) => {
                const guards = evaluateRowGuards(m);
                const roleBadge = getRoleBadgeStyle(m.rol);

                return (
                  <tr key={m.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>{m.nombres}</span>
                          {guards.isSelf && (
                            <span
                              style={{
                                padding: '2px 6px',
                                borderRadius: '8px',
                                fontSize: '10px',
                                fontWeight: 700,
                                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                                color: '#1d4ed8',
                              }}
                            >
                              Tú (Sesión actual)
                            </span>
                          )}
                        </div>
                        {m.username && (
                          <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>
                            @{m.username}
                          </span>
                        )}
                      </div>
                    </td>

                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {m.telefono}
                    </td>

                    <td style={{ padding: '12px 16px' }}>
                      <select
                        value={(m.rol as string) === 'admin' ? 'administrador' : (m.rol as string) === 'supervisor' ? 'jefe_taller' : m.rol}
                        onChange={(e) => handleSeleccionarRol(m, e.target.value as MecanicoRol)}
                        disabled={(guards.isSelf && guards.isAdmin) || guards.restrictedByHierarchy}
                        style={{
                          padding: '4px 8px',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--border-color)',
                          fontSize: '12px',
                          fontWeight: 600,
                          backgroundColor: roleBadge.bg,
                          color: roleBadge.color,
                          cursor: (guards.isSelf && guards.isAdmin) || guards.restrictedByHierarchy ? 'not-allowed' : 'pointer',
                        }}
                      >
                        <option value="mecanico">Mecánico</option>
                        <option value="jefe_taller">Jefe de Taller</option>
                        {esAdmin && <option value="administrador">Administrador</option>}
                      </select>
                    </td>

                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        {m.bloqueado ? (
                          <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#b91c1c' }}>
                            Bloqueado
                          </span>
                        ) : m.activo ? (
                          <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#047857' }}>
                            Activo
                          </span>
                        ) : (
                          <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#b45309' }}>
                            Inactivo
                          </span>
                        )}
                      </div>
                    </td>

                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {m.total_diagnosticos} realizados
                    </td>

                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px', alignItems: 'center' }}>
                        {/* Editar Perfil Button */}
                        <button
                          type="button"
                          onClick={() => handleAbrirModalEditar(m)}
                          disabled={!guards.canEdit}
                          title={guards.editTooltip || 'Editar datos del personal'}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '5px 10px',
                            backgroundColor: guards.canEdit ? 'rgba(59, 130, 246, 0.1)' : '#f1f5f9',
                            color: guards.canEdit ? '#2563eb' : '#94a3b8',
                            border: 'none',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            fontWeight: 600,
                            cursor: guards.canEdit ? 'pointer' : 'not-allowed',
                            opacity: guards.canEdit ? 1 : 0.6,
                          }}
                        >
                          <Pencil size={13} />
                          <span>Editar</span>
                        </button>

                        {/* Activar / Desactivar Button */}
                        <button
                          type="button"
                          onClick={() => setConfirmActivarModal({ mecanico: m, estaActivando: !m.activo })}
                          disabled={!guards.canToggleActive}
                          title={guards.activeTooltip}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '5px 10px',
                            backgroundColor: guards.canToggleActive ? (m.activo ? 'rgba(245, 158, 11, 0.1)' : 'rgba(16, 185, 129, 0.1)') : '#f1f5f9',
                            color: guards.canToggleActive ? (m.activo ? '#b45309' : '#047857') : '#94a3b8',
                            border: 'none',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            fontWeight: 600,
                            cursor: guards.canToggleActive ? 'pointer' : 'not-allowed',
                            opacity: guards.canToggleActive ? 1 : 0.6,
                          }}
                        >
                          <Power size={13} />
                          <span>{m.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>

                        {/* Bloquear / Desbloquear Button */}
                        <button
                          type="button"
                          onClick={() => setConfirmBloquearModal({ mecanico: m, estaBloqueando: !m.bloqueado })}
                          disabled={!guards.canToggleBlock}
                          title={guards.blockTooltip}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '5px 10px',
                            backgroundColor: guards.canToggleBlock ? (m.bloqueado ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)') : '#f1f5f9',
                            color: guards.canToggleBlock ? (m.bloqueado ? '#047857' : '#b91c1c') : '#94a3b8',
                            border: 'none',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            fontWeight: 600,
                            cursor: guards.canToggleBlock ? 'pointer' : 'not-allowed',
                            opacity: guards.canToggleBlock ? 1 : 0.6,
                          }}
                        >
                          {m.bloqueado ? <Unlock size={13} /> : <Lock size={13} />}
                          <span>{m.bloqueado ? 'Desbloquear' : 'Bloquear'}</span>
                        </button>

                        {/* Revocar Acceso Técnico */}
                        <button
                          type="button"
                          onClick={() => setConfirmRevocarModal(m)}
                          disabled={!guards.canRevoke}
                          title={guards.revokeTooltip}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '5px 10px',
                            backgroundColor: guards.canRevoke ? 'rgba(225, 29, 72, 0.1)' : '#f1f5f9',
                            color: guards.canRevoke ? '#e11d48' : '#94a3b8',
                            border: 'none',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            fontWeight: 600,
                            cursor: guards.canRevoke ? 'pointer' : 'not-allowed',
                            opacity: guards.canRevoke ? 1 : 0.6,
                          }}
                        >
                          <ShieldAlert size={13} />
                          <span>Revocar acceso</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Modal para Registrar Nuevo Personal */}
      {modalNuevoAbierto && (
        <Modal
          isOpen={modalNuevoAbierto}
          onClose={() => setModalNuevoAbierto(false)}
          title="Registrar Nuevo Personal del Taller"
          maxWidth="480px"
        >
          <form onSubmit={handleCrearNuevoMecanico} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {errorNuevo && (
              <div style={{ padding: '10px 14px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: 'var(--radius-sm)', fontSize: '13px' }}>
                {errorNuevo}
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Nombres Completos <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="text"
                value={nuevoNombre}
                onChange={(e) => setNuevoNombre(e.target.value)}
                placeholder="Ej: Carlos Mendoza"
                required
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Nombre de Usuario (Login) <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>(Opcional)</span>
              </label>
              <input
                type="text"
                value={nuevoUsername}
                onChange={(e) => setNuevoUsername(e.target.value)}
                placeholder="Ej: cmendoza"
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box' }}
              />
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Identificador para iniciar sesión en la web.
              </p>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Teléfono / WhatsApp <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="text"
                value={nuevoTelefono}
                onChange={(e) => setNuevoTelefono(e.target.value)}
                placeholder="+51 987 654 321"
                required
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box' }}
              />
            </div>

            {nuevoRol === 'administrador' && <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Contraseña Inicial de Acceso <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="password"
                value={nuevoPassword}
                onChange={(e) => setNuevoPassword(e.target.value)}
                placeholder="Mínimo 12 caracteres (mayúsculas, minúsculas y números)"
                required
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box' }}
              />
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Política de seguridad: 12 caracteres mínimos con mayúsculas, minúsculas y números.
              </p>
            </div>}

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Rol Inicial <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                value={nuevoRol}
                onChange={(e) => setNuevoRol(e.target.value as MecanicoRol)}
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', backgroundColor: '#ffffff', boxSizing: 'border-box' }}
              >
                <option value="mecanico">Mecánico</option>
                <option value="jefe_taller">Jefe de Taller</option>
                {esAdmin && <option value="administrador">Administrador</option>}
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
              <button
                type="button"
                onClick={() => setModalNuevoAbierto(false)}
                disabled={guardandoNuevo}
                style={{ padding: '8px 16px', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', fontSize: '13px', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={guardandoNuevo}
                style={{ padding: '8px 18px', backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
              >
                {guardandoNuevo ? 'Guardando...' : 'Registrar Personal'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal confirmación para Activar / Desactivar Cuenta */}
      {confirmActivarModal && (
        <ConfirmModal
          isOpen={!!confirmActivarModal}
          onClose={() => setConfirmActivarModal(null)}
          onConfirm={ejecutarToggleActivar}
          cargando={procesandoActivar}
          title={confirmActivarModal.estaActivando ? 'Confirmar Activación de Cuenta' : 'Confirmar Desactivación de Cuenta'}
          variant={confirmActivarModal.estaActivando ? 'primary' : 'warning'}
          confirmText={confirmActivarModal.estaActivando ? 'Sí, Activar Cuenta' : 'Sí, Desactivar Cuenta'}
          message={
            <div>
              <p style={{ margin: '0 0 10px 0' }}>
                ¿Deseas <strong>{confirmActivarModal.estaActivando ? 'activar' : 'desactivar'}</strong> la cuenta de <strong>{confirmActivarModal.mecanico.nombres}</strong>?
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)' }}>
                {confirmActivarModal.estaActivando
                  ? 'El usuario podrá volver a ingresar al sistema del taller con sus credenciales.'
                  : 'El usuario no podrá iniciar sesión mientras su cuenta permanezca inactiva.'}
              </p>
            </div>
          }
        />
      )}

      {/* Modal confirmación para Bloquear / Desbloquear Cuenta */}
      {confirmBloquearModal && (
        <ConfirmModal
          isOpen={!!confirmBloquearModal}
          onClose={() => setConfirmBloquearModal(null)}
          onConfirm={ejecutarToggleBloquear}
          cargando={procesandoBloquear}
          title={confirmBloquearModal.estaBloqueando ? 'Confirmar Bloqueo de Acceso' : 'Confirmar Desbloqueo de Acceso'}
          variant={confirmBloquearModal.estaBloqueando ? 'danger' : 'primary'}
          confirmText={confirmBloquearModal.estaBloqueando ? 'Sí, Bloquear Acceso' : 'Sí, Desbloquear Acceso'}
          message={
            <div>
              <p style={{ margin: '0 0 10px 0' }}>
                ¿Deseas <strong>{confirmBloquearModal.estaBloqueando ? 'bloquear' : 'desbloquear'}</strong> el acceso a <strong>{confirmBloquearModal.mecanico.nombres}</strong>?
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)' }}>
                {confirmBloquearModal.estaBloqueando
                  ? 'El bloqueo impedirá totalmente el acceso tanto a la plataforma como al canal WhatsApp.'
                  : 'Se levantará la restricción y el usuario podrá operar normalmente.'}
              </p>
            </div>
          }
        />
      )}

      {/* Modal confirmación para Todo Cambio de Rol */}
      {confirmRolModal && (
        <ConfirmModal
          isOpen={!!confirmRolModal}
          onClose={() => { setConfirmRolModal(null); setPasswordNuevoAdmin(''); }}
          onConfirm={() => ejecutarCambioRol(confirmRolModal.mecanico.id, confirmRolModal.nuevoRol)}
          cargando={procesandoRol}
          title="Confirmar Modificación de Rol"
          variant="warning"
          confirmText="Sí, Cambiar Rol"
          message={
            <div>
              <p style={{ margin: '0 0 10px 0' }}>
                ¿Deseas cambiar el rol de <strong>{confirmRolModal.mecanico.nombres}</strong> de <strong>{confirmRolModal.mecanico.rol}</strong> a <strong>{confirmRolModal.nuevoRol}</strong>?
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: '#92400e' }}>
                {confirmRolModal.nuevoRol === 'administrador'
                  ? 'Esta cuenta obtendrá acceso exclusivo al panel web y deberá cambiar la contraseña al ingresar.'
                  : 'Esta cuenta dejará de tener credenciales web y trabajará únicamente mediante WhatsApp.'}
              </p>
              {confirmRolModal.nuevoRol === 'administrador' && (
                <input
                  type="password"
                  value={passwordNuevoAdmin}
                  onChange={(e) => setPasswordNuevoAdmin(e.target.value)}
                  placeholder="Contraseña inicial (mínimo 12 caracteres)"
                  style={{ width: '100%', marginTop: '12px', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid #f59e0b', boxSizing: 'border-box' }}
                />
              )}
            </div>
          }
        />
      )}

      {/* Modal confirmación para Revocar Acceso Técnico */}
      {confirmRevocarModal && (
        <ConfirmModal
          isOpen={!!confirmRevocarModal}
          onClose={() => setConfirmRevocarModal(null)}
          onConfirm={handleConfirmarRevocacion}
          cargando={procesandoRevocacion}
          title="Confirmar Revocación de Acceso Técnico"
          variant="danger"
          confirmText="Sí, Revocar Acceso"
          message={
            <div>
              <p style={{ margin: '0 0 10px 0' }}>
                ¿Deseas revocar el acceso técnico de <strong>{confirmRevocarModal.nombres}</strong>?
              </p>
              <p style={{ margin: 0, fontSize: '12px', color: '#475569', lineHeight: 1.4 }}>
                🛡️ <strong>Aviso:</strong> El usuario perderá sus permisos técnicos y volverá a tener rol de cliente. Se conservará íntegramente todo su historial de diagnósticos y conversaciones asociadas.
              </p>
            </div>
          }
        />
      )}

      {/* Modal para Editar Perfil del Mecánico / Personal */}
      {mecanicoAEditar && (
        <Modal
          isOpen={!!mecanicoAEditar}
          onClose={() => {
            if (!guardandoEdicion) {
              setMecanicoAEditar(null);
              setErrorEdicion(null);
            }
          }}
          title={`Editar Perfil: ${mecanicoAEditar.nombres}`}
          maxWidth="480px"
        >
          <form onSubmit={handleGuardarEdicion} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {errorEdicion && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 14px',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  color: '#b91c1c',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                }}
              >
                <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                <span>{errorEdicion}</span>
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Nombres Completos <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="text"
                value={editNombres}
                onChange={(e) => setEditNombres(e.target.value)}
                placeholder="Ej: Carlos Mendoza"
                required
                disabled={guardandoEdicion}
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box' }}
              />
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Nombre y apellido real de la persona para reportes y diagnósticos.
              </p>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Nombre de Usuario (Login) <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>(Opcional)</span>
              </label>
              <input
                type="text"
                value={editUsername}
                onChange={(e) => setEditUsername(e.target.value)}
                placeholder="Ej: cmendoza"
                disabled={guardandoEdicion}
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box' }}
              />
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Identificador para iniciar sesión en la web.
              </p>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
                  Teléfono / WhatsApp <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>(Opcional)</span>
                </label>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Actual: <strong>{mecanicoAEditar.telefono}</strong>
                </span>
              </div>
              <input
                type="text"
                value={editTelefono}
                onChange={(e) => setEditTelefono(e.target.value)}
                placeholder="Dejar en blanco para conservar el actual"
                disabled={guardandoEdicion}
                style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box' }}
              />
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Ingrese el nuevo número con formato internacional solo si desea cambiarlo.
              </p>
            </div>

            {(mecanicoAEditar.rol === 'administrador' || (mecanicoAEditar.rol as string) === 'admin') && (
              <div style={{ padding: '12px', backgroundColor: 'var(--bg-main)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', cursor: 'pointer', margin: 0 }}>
                  <input
                    type="checkbox"
                    checked={deseaCambiarPassword}
                    onChange={(e) => {
                      setDeseaCambiarPassword(e.target.checked);
                      if (!e.target.checked) setEditPassword('');
                    }}
                    disabled={guardandoEdicion}
                  />
                  <span>Deseo cambiar la contraseña de acceso web</span>
                </label>

                {deseaCambiarPassword && (
                  <div style={{ marginTop: '4px' }}>
                    <input
                      type="password"
                      value={editPassword}
                      onChange={(e) => setEditPassword(e.target.value)}
                      placeholder="Nueva contraseña (mínimo 12 caracteres)"
                      autoComplete="new-password"
                      disabled={guardandoEdicion}
                      style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '13px', boxSizing: 'border-box', backgroundColor: '#ffffff' }}
                    />
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                      Mínimo 12 caracteres (mayúsculas, minúsculas y números).
                    </p>
                  </div>
                )}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
              <button
                type="button"
                onClick={() => {
                  setMecanicoAEditar(null);
                  setErrorEdicion(null);
                }}
                disabled={guardandoEdicion}
                style={{ padding: '8px 16px', backgroundColor: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', fontSize: '13px', color: 'var(--text-secondary)', cursor: guardandoEdicion ? 'not-allowed' : 'pointer' }}
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={guardandoEdicion}
                style={{
                  padding: '8px 18px',
                  backgroundColor: '#3b82f6',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: guardandoEdicion ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                {guardandoEdicion && <Loader2 size={14} className="animate-spin" />}
                <span>{guardandoEdicion ? 'Guardando...' : 'Guardar Cambios'}</span>
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
