import { useState, useCallback } from 'react';
import { diagnosticsApi } from '../features/management/api/diagnosticsApi';
import type { Diagnostico, EstadoDiagnostico } from '../types';
import { getErrorMessage } from '../utils/errors';

export function useDiagnosticos() {
  const [diagnosticos, setDiagnosticos] = useState<Diagnostico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarDiagnosticos = useCallback(async (filtros?: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
  }) => {
    setCargando(true);
    setError(null);
    try {
      const data = await diagnosticsApi.listar(filtros);
      setDiagnosticos(data);
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Error al cargar el historial de diagnósticos'));
    } finally {
      setCargando(false);
    }
  }, []);

  const actualizarEstado = useCallback(async (
    id: string,
    nuevoEstado: EstadoDiagnostico,
    notas?: string
  ) => {
    await diagnosticsApi.actualizarEstado({
      diagnostico_id: id,
      nuevo_estado: nuevoEstado,
      notas_mecanico: notas,
    });
    await cargarDiagnosticos();
  }, [cargarDiagnosticos]);

  return {
    diagnosticos,
    cargando,
    error,
    cargarDiagnosticos,
    actualizarEstado,
  };
}
