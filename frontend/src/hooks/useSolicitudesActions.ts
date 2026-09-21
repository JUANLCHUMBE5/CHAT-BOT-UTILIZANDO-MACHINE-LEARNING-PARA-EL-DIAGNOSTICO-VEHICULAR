import { useState } from 'react';
import type { SolicitudAcceso } from '../types';
import { apiService } from '../services/api';
import { getErrorMessage } from '../utils/errors';

export interface UseSolicitudesActionsProps {
  onRecargar: () => void;
}

export const useSolicitudesActions = ({ onRecargar }: UseSolicitudesActionsProps) => {
  const [subSeccion, setSubSeccion] = useState<'pendientes' | 'historial'>('pendientes');

  // Approval modal state
  const [modalAprobado, setModalAprobado] = useState<{
    abierto: boolean;
    nombreUsuario: string;
    telefono: string;
  } | null>(null);
  const [aprobandoId, setAprobandoId] = useState<string | null>(null);

  // Rejection modal state
  const [modalRechazo, setModalRechazo] = useState<{
    abierto: boolean;
    solicitud: SolicitudAcceso | null;
  } | null>(null);
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [rechazando, setRechazando] = useState(false);
  const [errorRechazo, setErrorRechazo] = useState<string | null>(null);

  // Notification error banner
  const [notificacionError, setNotificacionError] = useState<string | null>(null);

  const handleAprobarSolicitud = async (sol: SolicitudAcceso) => {
    setAprobandoId(sol.id);
    setNotificacionError(null);
    try {
      await apiService.aprobarSolicitudAcceso(sol.id);
      setModalAprobado({
        abierto: true,
        nombreUsuario: sol.usuario_nombre,
        telefono: sol.telefono,
      });
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al aprobar la solicitud'));
    } finally {
      setAprobandoId(null);
    }
  };

  const handleAbrirModalRechazo = (sol: SolicitudAcceso) => {
    setModalRechazo({ abierto: true, solicitud: sol });
    setMotivoRechazo('');
    setErrorRechazo(null);
  };

  const handleConfirmarRechazo = async () => {
    if (!modalRechazo?.solicitud) return;
    const motivoTrimmed = motivoRechazo.trim();
    if (!motivoTrimmed) {
      setErrorRechazo('El motivo de rechazo es obligatorio y no puede estar vacío.');
      return;
    }

    setRechazando(true);
    setErrorRechazo(null);
    try {
      await apiService.rechazarSolicitudAcceso(modalRechazo.solicitud.id, motivoTrimmed);
      setModalRechazo(null);
      setMotivoRechazo('');
      onRecargar();
    } catch (error: unknown) {
      setErrorRechazo(getErrorMessage(error, 'Error al rechazar la solicitud'));
    } finally {
      setRechazando(false);
    }
  };

  return {
    subSeccion,
    setSubSeccion,
    modalAprobado,
    setModalAprobado,
    aprobandoId,
    modalRechazo,
    setModalRechazo,
    motivoRechazo,
    setMotivoRechazo,
    rechazando,
    errorRechazo,
    notificacionError,
    setNotificacionError,
    handleAprobarSolicitud,
    handleAbrirModalRechazo,
    handleConfirmarRechazo,
  };
};
