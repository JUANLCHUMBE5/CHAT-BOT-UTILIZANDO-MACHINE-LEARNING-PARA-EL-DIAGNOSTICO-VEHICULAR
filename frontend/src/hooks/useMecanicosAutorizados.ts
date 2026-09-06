import { useState, useMemo } from 'react';
import type { Mecanico } from '../types';
import { apiService } from '../services/api';
import { getErrorMessage } from '../utils/errors';

export interface UseMecanicosAutorizadosProps {
  mecanicos: Mecanico[];
  onRecargar: () => void;
}

export const useMecanicosAutorizados = ({
  mecanicos,
  onRecargar,
}: UseMecanicosAutorizadosProps) => {
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'bloqueados'>('todos');

  // Feedback notifications
  const [notificacionError, setNotificacionError] = useState<string | null>(null);
  const [notificacionExito, setNotificacionExito] = useState<string | null>(null);

  // Confirmation Modals
  const [confirmBloquearModal, setConfirmBloquearModal] = useState<{
    mecanico: Mecanico;
    estaBloqueando: boolean;
  } | null>(null);
  const [procesandoBloquear, setProcesandoBloquear] = useState(false);

  const [confirmRevocarModal, setConfirmRevocarModal] = useState<Mecanico | null>(null);
  const [procesandoRevocacion, setProcesandoRevocacion] = useState(false);

  // Filtrado de mecánicos
  const mecanicosFiltrados = useMemo(() => {
    return mecanicos.filter((m) => {
      const cumpleBusqueda =
        !busqueda ||
        m.nombres.toLowerCase().includes(busqueda.toLowerCase()) ||
        m.telefono.includes(busqueda);

      if (!cumpleBusqueda) return false;

      if (filtroEstado === 'activos') return m.activo && !m.bloqueado;
      if (filtroEstado === 'bloqueados') return m.bloqueado;
      return true;
    });
  }, [mecanicos, busqueda, filtroEstado]);

  const totalActivos = mecanicos.filter((m) => m.activo && !m.bloqueado).length;
  const totalBloqueados = mecanicos.filter((m) => m.bloqueado).length;

  const handleToggleBloquear = async () => {
    if (!confirmBloquearModal) return;
    setProcesandoBloquear(true);
    setNotificacionError(null);
    setNotificacionExito(null);

    const { mecanico, estaBloqueando } = confirmBloquearModal;
    try {
      await apiService.toggleBloquearMecanico(mecanico.id);
      setNotificacionExito(
        estaBloqueando
          ? `Mecánico "${mecanico.nombres}" bloqueado. Ya no podrá consultar diagnósticos por WhatsApp.`
          : `Mecánico "${mecanico.nombres}" desbloqueado exitosamente.`
      );
      setConfirmBloquearModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al cambiar estado de bloqueo del mecánico'));
    } finally {
      setProcesandoBloquear(false);
    }
  };

  const handleRevocarAcceso = async () => {
    if (!confirmRevocarModal) return;
    setProcesandoRevocacion(true);
    setNotificacionError(null);
    setNotificacionExito(null);

    try {
      await apiService.revocarAccesoMecanico(confirmRevocarModal.id);
      setNotificacionExito(
        `Acceso técnico revocado para "${confirmRevocarModal.nombres}". El usuario regresa al rol de cliente sin acceso técnico.`
      );
      setConfirmRevocarModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al revocar acceso del mecánico'));
    } finally {
      setProcesandoRevocacion(false);
    }
  };

  return {
    busqueda,
    setBusqueda,
    filtroEstado,
    setFiltroEstado,
    notificacionError,
    setNotificacionError,
    notificacionExito,
    setNotificacionExito,
    confirmBloquearModal,
    setConfirmBloquearModal,
    procesandoBloquear,
    confirmRevocarModal,
    setConfirmRevocarModal,
    procesandoRevocacion,
    mecanicosFiltrados,
    totalActivos,
    totalBloqueados,
    handleToggleBloquear,
    handleRevocarAcceso,
  };
};
