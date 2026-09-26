import { useState, useMemo } from 'react';
import type { Mecanico } from '../types';
import { apiService } from '../services/api';
import { getErrorMessage } from '../utils/errors';
import { calcularVigenciaMecanico } from '../utils/vigenciaMecanico';

export type FiltroEstadoMecanico = 'todos' | 'activos' | 'por_vencer' | 'inactivos_bloqueados';

export interface UseMecanicosAutorizadosProps {
  mecanicos: Mecanico[];
  onRecargar: () => void;
}

export const useMecanicosAutorizados = ({
  mecanicos,
  onRecargar,
}: UseMecanicosAutorizadosProps) => {
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState<FiltroEstadoMecanico>('activos');

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

  // Filtrado de mecánicos con vigencia derivada
  const mecanicosFiltrados = useMemo(() => {
    return mecanicos.filter((m) => {
      const cumpleBusqueda =
        !busqueda ||
        (m.nombres && m.nombres.toLowerCase().includes(busqueda.toLowerCase())) ||
        (m.telefono && m.telefono.includes(busqueda));

      if (!cumpleBusqueda) return false;

      const vigencia = calcularVigenciaMecanico(m);

      if (filtroEstado === 'activos') {
        return vigencia.estadoVisual === 'activo';
      }
      if (filtroEstado === 'por_vencer') {
        return vigencia.estadoVisual === 'por_vencer';
      }
      if (filtroEstado === 'inactivos_bloqueados') {
        return vigencia.estadoVisual === 'bloqueado' || vigencia.estadoVisual === 'inactivo' || vigencia.estadoVisual === 'vencido';
      }
      return true;
    });
  }, [mecanicos, busqueda, filtroEstado]);

  const conteos = useMemo(() => {
    let activos = 0;
    let porVencer = 0;
    let inactivosBloqueados = 0;

    for (const m of mecanicos) {
      const vigencia = calcularVigenciaMecanico(m);
      if (vigencia.estadoVisual === 'activo') activos++;
      else if (vigencia.estadoVisual === 'por_vencer') porVencer++;
      else inactivosBloqueados++;
    }

    return { activos, porVencer, inactivosBloqueados };
  }, [mecanicos]);

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
    totalActivos: conteos.activos,
    totalPorVencer: conteos.porVencer,
    totalInactivosBloqueados: conteos.inactivosBloqueados,
    handleToggleBloquear,
    handleRevocarAcceso,
  };
};
