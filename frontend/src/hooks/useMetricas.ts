import { useState, useCallback } from 'react';
import { apiService } from '../services/api';
import type { ResumenMetricas } from '../types';
import { getErrorMessage } from '../utils/errors';

export function useMetricas() {
  const [metricas, setMetricas] = useState<ResumenMetricas | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarMetricas = useCallback(async (fechaInicio?: string, fechaFin?: string) => {
    setCargando(true);
    setError(null);
    try {
      const data = await apiService.getResumenMetricas(fechaInicio, fechaFin);
      setMetricas(data);
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Error al cargar las métricas ejecutivas'));
    } finally {
      setCargando(false);
    }
  }, []);

  return {
    metricas,
    cargando,
    error,
    cargarMetricas,
  };
}
